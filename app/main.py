import os
import logging
import shutil
import tempfile
import uuid

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from scalar_fastapi import get_scalar_api_reference

from .transcribe import transcribe_audio
from .diarize import diarize_audio
from .align import align_transcript_with_speakers
from .roles import assign_teacher_student
from .metrics import compute_metrics
from .filters import clean_text

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Classroom Voice Analytics API",
    description="MVP prototype: classroom audio -> transcript + teacher/student engagement metrics",
    version="0.1.0",
)

DEMO_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Classroom Voice Analytics Demo</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 2rem; background: #f7f7fb; color: #222; }
    .card { max-width: 1000px; margin: 0 auto; background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
    input[type=file], button { margin-top: 0.75rem; }
    button { padding: 0.7rem 1.1rem; border: 0; border-radius: 8px; background: #1f6feb; color: white; cursor: pointer; }
    button:disabled { background: #8aaed7; cursor: wait; }
    .status { margin-top: 1rem; color: #3a3a3a; }
    .status.error { color: #b42318; }
    .status.success { color: #147a43; }
    .file-name { margin-top: 0.5rem; color: #555; font-size: 0.9rem; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .box { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; background: #fafafa; }
    .transcript { white-space: pre-wrap; line-height: 1.5; }
    .metric-list { list-style: none; padding-left: 0; }
    .metric-list li { margin: 0.4rem 0; }
    .summary { font-weight: 600; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Classroom Voice Analytics</h1>
    <p>Upload a classroom audio file to generate a transcript, role labels, and engagement metrics.</p>

    <form id="uploadForm" method="post" action="/api/v1/full-report" enctype="multipart/form-data">
      <label for="audioFile">Audio file</label>
      <input id="audioFile" name="audio_file" type="file" accept="audio/*" required />
      <button id="submitBtn" type="submit">Submit</button>
    </form>
    <div id="fileName" class="file-name">No file selected.</div>
    <div id="status" class="status">Waiting for audio upload.</div>

    <div id="results" style="display:none; margin-top:2rem;">
      <div class="summary" id="summary"></div>
      <div class="grid" style="margin-top:1rem;">
        <div class="box">
          <h3>Metrics</h3>
          <ul id="metrics" class="metric-list"></ul>
        </div>
        <div class="box">
          <h3>Roles</h3>
          <pre id="roles"></pre>
        </div>
      </div>
      <div class="box" style="margin-top:1rem;">
        <h3>Transcript</h3>
        <div id="transcript" class="transcript"></div>
      </div>
    </div>
  </div>

  <script>
    const submitBtn = document.getElementById('submitBtn');
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('audioFile');
    const fileNameEl = document.getElementById('fileName');
    const statusEl = document.getElementById('status');
    const resultsEl = document.getElementById('results');
    const metricsEl = document.getElementById('metrics');
    const transcriptEl = document.getElementById('transcript');
    const rolesEl = document.getElementById('roles');
    const summaryEl = document.getElementById('summary');
    const apiBase = new URLSearchParams(window.location.search).get('api_base') || window.location.origin;

    fileInput.addEventListener('change', () => {
      fileNameEl.textContent = fileInput.files[0]
        ? `Selected: ${fileInput.files[0].name}`
        : 'No file selected.';
      statusEl.className = 'status';
      statusEl.textContent = 'Ready to analyze.';
    });

    function renderMetrics(metrics) {
      metricsEl.innerHTML = '';
      for (const [key, value] of Object.entries(metrics || {})) {
        const item = document.createElement('li');
        item.textContent = `${key}: ${value}`;
        metricsEl.appendChild(item);
      }
    }

    function renderTranscript(transcript) {
      transcriptEl.textContent = (transcript || [])
        .map((seg) => `[${seg.speaker || 'UNKNOWN'}] ${seg.text || ''}`)
        .join('\n');
    }

    function renderSummary(metrics) {
      const teacherPct = Number(metrics.teacher_dominance_ratio || 0) * 100;
      const studentPct = Number(metrics.student_participation_indicator || 0) * 100;
      const interactions = Number(metrics.interaction_count || 0);
      const teacherQuestions = Number(metrics.teacher_questions || 0);
      summaryEl.textContent = `Teacher spoke for ${teacherPct.toFixed(0)}% of the session across ${interactions} interaction turns, asking ${teacherQuestions} questions; students accounted for ${studentPct.toFixed(0)}% of speaking time.`;
    }

    uploadForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const file = fileInput.files[0];
      if (!file) {
        statusEl.textContent = 'Please choose an audio file first.';
        statusEl.className = 'status error';
        return;
      }

      if (!file.type.startsWith('audio/') && !/\.(wav|mp3|m4a|ogg|flac|webm)$/i.test(file.name)) {
        statusEl.textContent = 'Please select a supported audio file.';
        statusEl.className = 'status error';
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = 'Processing...';
      statusEl.className = 'status';
      statusEl.textContent = 'Uploading and processing audio. This can take several minutes for a long classroom recording...';
      resultsEl.style.display = 'none';

      const formData = new FormData(uploadForm);

      try {
        const response = await fetch(`${apiBase}/api/v1/full-report`, {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Request failed (${response.status}): ${errorText}`);
        }

        const data = await response.json();
        renderMetrics(data.metrics || {});
        renderTranscript(data.transcript || []);
        rolesEl.textContent = JSON.stringify(data.roles || {}, null, 2);
        renderSummary(data.metrics || {});
        resultsEl.style.display = 'block';
        statusEl.className = 'status success';
        statusEl.textContent = 'Analysis complete.';
      } catch (error) {
        statusEl.className = 'status error';
        statusEl.textContent = error.message || 'Analysis failed. Please try again.';
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit';
      }
    });
  </script>
</body>
</html>
"""

@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
  return HTMLResponse(
    DEMO_HTML,
    headers={
      "Cache-Control": "no-store, no-cache, must-revalidate",
      "Pragma": "no-cache",
    },
  )

@app.get("/", response_class=HTMLResponse)
async def root_redirect():
    return HTMLResponse("<html><body><p>API running. Use /demo for the uploader interface or /scalar for API docs.</p></body></html>")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for an MVP demo; tighten for anything real
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    """Scalar-rendered API reference (nicer alternative to default Swagger UI)."""
    return get_scalar_api_reference(openapi_url=app.openapi_url, title=app.title)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/v1/full-report")
def full_report(audio_file: UploadFile = File(...)):
    """
    Convenience endpoint chaining the whole pipeline:
    transcribe -> diarize -> align -> clean -> assign roles -> compute metrics.

    This is the one your demo UI should call.
    """
    suffix = os.path.splitext(audio_file.filename or "audio.wav")[1] or ".wav"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uuid.uuid4()}{suffix}") as f:
            temp_path = f.name
            shutil.copyfileobj(audio_file.file, f)

        logger.info("Processing uploaded audio: %s", audio_file.filename or "unnamed file")
        logger.info("Transcribing audio...")
        transcript_segments, info = transcribe_audio(temp_path)
        logger.info(
            "Transcription complete: detected_language=%s segments=%d",
            info.language,
            len(transcript_segments),
        )

        logger.info("Diarizing audio on CPU...")
        speaker_turns = diarize_audio(temp_path)
        logger.info("Diarization complete: turns=%d", len(speaker_turns))

        aligned = align_transcript_with_speakers(transcript_segments, speaker_turns)
        logger.info("Aligned transcript with speaker turns")

        for seg in aligned:
            seg["text"] = clean_text(seg["text"])

        role_map = assign_teacher_student(speaker_turns)
        metrics = compute_metrics(speaker_turns, aligned, role_map)
        logger.info("Analysis complete: roles=%s", role_map)

        return {
            "detected_language": info.language,
            "roles": role_map,
            "transcript": aligned,
            "metrics": metrics,
        }
    except Exception:
        logger.exception("Full-report processing failed")
        raise
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
