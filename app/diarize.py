"""
Step 2 of the pipeline: Audio -> "who spoke when".

pyannote does NOT understand language or words — it clusters the audio purely
by voice/acoustic similarity into anonymous speaker labels (SPEAKER_00,
SPEAKER_01, ...). Mapping those labels to "Teacher"/"Student" happens later,
in roles.py.

Requires a Hugging Face token with access accepted on:
  - pyannote/speaker-diarization-3.1
  - pyannote/segmentation-3.0 (its dependency)
Both are instant click-through approvals, not manual review.
"""
import torchaudio

if not hasattr(torchaudio, "AudioMetaData"):
    torchaudio.AudioMetaData = object
if not hasattr(torchaudio, "list_audio_backends"):
    torchaudio.list_audio_backends = lambda: ["soundfile"]

from pyannote.audio import Pipeline
from .config import HF_TOKEN

_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        if not HF_TOKEN:
            raise RuntimeError(
                "HF_TOKEN not set. Add it to your .env file — see .env.example."
            )
        try:
            _pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1", token=HF_TOKEN
            )
        except TypeError:
            # Older pyannote.audio versions use the pre-rename parameter name.
            _pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1", use_auth_token=HF_TOKEN
            )
    return _pipeline


def diarize_audio(audio_path: str):
    pipeline = _get_pipeline()
    diarization = pipeline(audio_path)
    turns = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        turns.append({"start": turn.start, "end": turn.end, "speaker": speaker})
    return turns