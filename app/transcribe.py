"""
Step 1 of the pipeline: Audio -> Text.

Uses faster-whisper (CTranslate2-backed Whisper) running fully offline once the
model weights are cached locally on first run.

task="translate" makes Whisper output English text directly, regardless of the
spoken language (Hindi, in our case). This is a single-model-call shortcut —
no separate translation step or API needed. If you'd rather keep the transcript
in Hindi (Devanagari script), switch task to "transcribe" instead.
"""
from faster_whisper import WhisperModel
from .config import WHISPER_MODEL_SIZE

_model = None


def _get_model():
    global _model
    if _model is None:
        # compute_type="int8" keeps this fast and light enough for CPU-only inference
        _model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def transcribe_audio(audio_path: str, task: str = "translate"):
    model = _get_model()
    segments, info = model.transcribe(
        audio_path,
        task=task,
        vad_filter=True,  # skips silent stretches, speeds things up and avoids junk output
    )
    results = [{"start": seg.start, "end": seg.end, "text": seg.text.strip()} for seg in segments]
    return results, info
