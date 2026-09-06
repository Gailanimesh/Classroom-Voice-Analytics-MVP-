"""
Run this against a SHORT clip (2-3 min, cut from your 40-min recording with
ffmpeg) BEFORE running the full file through the API. This is a fast sanity
check on the whole chain without waiting through a long transcription run.

Cut a short clip first, e.g.:
    ffmpeg -i full_recording.mp3 -ss 00:05:00 -t 00:02:00 short_clip.wav

Usage:
    python -m tests.test_pipeline_manual path/to/short_clip.wav
"""
import sys

from app.transcribe import transcribe_audio
from app.diarize import diarize_audio
from app.align import align_transcript_with_speakers
from app.roles import assign_teacher_student
from app.metrics import compute_metrics
from app.filters import clean_text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m tests.test_pipeline_manual path/to/short_clip.wav")
        sys.exit(1)

    audio_path = sys.argv[1]

    print("Transcribing...")
    segments, info = transcribe_audio(audio_path)
    print(f"Detected language: {info.language}")

    print("Diarizing...")
    turns = diarize_audio(audio_path)
    print("Distinct speakers found:", set(t["speaker"] for t in turns))

    aligned = align_transcript_with_speakers(segments, turns)
    for seg in aligned:
        seg["text"] = clean_text(seg["text"])

    role_map = assign_teacher_student(turns)
    metrics = compute_metrics(turns, aligned, role_map)

    print("\n--- Roles ---")
    print(role_map)

    print("\n--- Transcript sample (first 5 segments) ---")
    for seg in aligned[:5]:
        print(f"[{seg['start']:.1f}-{seg['end']:.1f}] {role_map.get(seg['speaker'], seg['speaker'])}: {seg['text']}")

    print("\n--- Metrics ---")
    for k, v in metrics.items():
        print(f"{k}: {v}")
