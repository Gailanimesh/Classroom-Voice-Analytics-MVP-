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
import huggingface_hub
import torch
import torchaudio
from collections import namedtuple

if not hasattr(torchaudio, "AudioMetaData"):
    torchaudio.AudioMetaData = object
if not hasattr(torchaudio, "list_audio_backends"):
    torchaudio.list_audio_backends = lambda: ["soundfile"]
if not hasattr(torchaudio, "info"):
    from torchcodec.decoders import AudioDecoder

    _AudioMetaData = namedtuple(
        "AudioMetaData",
        ["sample_rate", "num_frames", "num_channels", "bits_per_sample", "encoding"],
    )
    torchaudio.AudioMetaData = _AudioMetaData

    def _torchaudio_info(file, backend=None):
        metadata = AudioDecoder(file).metadata
        return _AudioMetaData(
            sample_rate=metadata.sample_rate,
            num_frames=metadata.num_frames,
            num_channels=metadata.num_channels,
            bits_per_sample=getattr(metadata, "bits_per_sample", 0),
            encoding=getattr(metadata, "codec", "unknown"),
        )

    torchaudio.info = _torchaudio_info

from pyannote.audio.core.task import Problem, Resolution, Specifications

if hasattr(torch.serialization, "add_safe_globals"):
    torch.serialization.add_safe_globals(
        [
            torch.torch_version.TorchVersion,
            Specifications,
            Problem,
            Resolution,
            getattr,
        ]
    )

_hf_hub_download = huggingface_hub.hf_hub_download


def _hf_hub_download_compat(*args, use_auth_token=None, **kwargs):
    if use_auth_token is not None and "token" not in kwargs:
        kwargs["token"] = use_auth_token
    return _hf_hub_download(*args, **kwargs)


huggingface_hub.hf_hub_download = _hf_hub_download_compat

from pyannote.audio import Pipeline
import pyannote.audio.core.model as _pyannote_model
import pyannote.audio.core.pipeline as _pyannote_pipeline

_pyannote_model.hf_hub_download = _hf_hub_download_compat
_pyannote_pipeline.hf_hub_download = _hf_hub_download_compat

from .config import HF_TOKEN

_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        if not HF_TOKEN:
            raise RuntimeError(
                "HF_TOKEN not set. Add it to your .env file — see .env.example."
            )
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