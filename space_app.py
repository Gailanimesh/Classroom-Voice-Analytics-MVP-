import logging
from pathlib import Path

import gradio as gr
try:
    import spaces
except ImportError:
    class _LocalSpaces:
        @staticmethod
        def GPU(**_kwargs):
            return lambda function: function

    spaces = _LocalSpaces()

from app.align import align_transcript_with_speakers
from app.diarize import diarize_audio
from app.filters import clean_text
from app.metrics import compute_metrics
from app.roles import assign_teacher_student
from app.transcribe import transcribe_audio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@spaces.GPU(duration=300)
def analyze_audio(audio_path):
    if not audio_path:
        raise gr.Error("Please choose an audio file first.")

    source_path = Path(audio_path)
    logger.info("Processing uploaded audio: %s", source_path.name)

    try:
        logger.info("Transcribing audio...")
        transcript_segments, info = transcribe_audio(str(source_path))
        logger.info(
            "Transcription complete: detected_language=%s segments=%d",
            info.language,
            len(transcript_segments),
        )

        logger.info("Diarizing audio on CPU...")
        speaker_turns = diarize_audio(str(source_path))
        logger.info("Diarization complete: turns=%d", len(speaker_turns))

        aligned = align_transcript_with_speakers(transcript_segments, speaker_turns)
        for segment in aligned:
            segment["text"] = clean_text(segment["text"])

        role_map = assign_teacher_student(speaker_turns)
        metrics = compute_metrics(speaker_turns, aligned, role_map)
        logger.info("Analysis complete: roles=%s", role_map)

        transcript_text = "\n".join(
            f"[{segment['start']:.1f}-{segment['end']:.1f}] "
            f"{role_map.get(segment['speaker'], segment['speaker'])}: {segment['text']}"
            for segment in aligned
        )
        report = {
            "detected_language": info.language,
            "roles": role_map,
            "transcript": aligned,
            "metrics": metrics,
        }
        status = (
            f"Analysis complete. Detected language: {info.language}. "
            f"Transcript segments: {len(aligned)}."
        )
        return status, metrics, role_map, transcript_text, report
    except Exception:
        logger.exception("Gradio analysis failed")
        raise gr.Error("Analysis failed. Check the Space logs for details.")


with gr.Blocks(title="Classroom Voice Analytics") as demo:
    gr.Markdown("# Classroom Voice Analytics\nUpload classroom audio to generate transcript and engagement metrics.")
    audio = gr.File(label="Audio file", file_types=["audio"], type="filepath")
    analyze_button = gr.Button("Analyze audio", variant="primary")
    status = gr.Markdown("Select an audio file to begin.")

    with gr.Row():
        metrics = gr.JSON(label="Engagement metrics")
        roles = gr.JSON(label="Speaker roles")
    transcript = gr.Textbox(label="Transcript", lines=18, interactive=False)
    raw_report = gr.JSON(label="Full report", visible=False)

    analyze_button.click(
        analyze_audio,
        inputs=audio,
        outputs=[status, metrics, roles, transcript, raw_report],
    )


if __name__ == "__main__":
    demo.launch()
