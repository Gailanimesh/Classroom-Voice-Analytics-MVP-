---
title: Classroom Voice Analytics
sdk: gradio
sdk_version: 6.26.0
python_version: '3.11'
app_file: space_app.py
emoji: 📉
colorFrom: blue
colorTo: blue
short_description: AI-powered classroom voice analytics
license: mit
---

# Classroom Voice Analytics — MVP

A prototype that turns classroom audio into a transcript, teacher/student
speech breakdown, and basic engagement metrics. Built for the MakerGhat
Full Stack Developer pre-work assignment (Task 1).

> **Status:** MVP / prototype — not production-hardened. See "Assumptions &
> limitations" below.

## Project structure
```
app/
  config.py     - env/config loading
  transcribe.py - Whisper: audio -> text (task="translate", offline, local model)
  diarize.py    - pyannote: audio -> speaker turns
  align.py      - merges transcript segments with speaker turns by timestamp
  filters.py    - strips filler words Whisper doesn't reliably filter itself
  roles.py      - heuristic: most talk-time = Teacher, rest = Student
  metrics.py    - engagement metric calculations
  main.py       - FastAPI app, single /api/v1/full-report endpoint + Scalar docs
tests/
  test_pipeline_manual.py - quick manual runner for validating on a short clip
TASKS.md        - task checklist (kept up to date across sessions)
UPDATES.md      - session-by-session change log / persistent project memory
```

## Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your Hugging Face token
```

You'll need a free Hugging Face token with access accepted on
`pyannote/speaker-diarization-3.1` (and its dependency `pyannote/segmentation-3.0`)
— both are instant click-through approvals on huggingface.co.

## Running
**Quick manual test on a short clip (recommended before the full file):**
```bash
ffmpeg -i full_recording.mp3 -ss 00:05:00 -t 00:02:00 short_clip.wav
python -m tests.test_pipeline_manual short_clip.wav
```

**API server:**
```bash
uvicorn app.main:app --reload
```
Then visit `http://localhost:8000/scalar` for interactive API docs, or POST
an audio file to `/api/v1/full-report`.

## Development approach
1. Whisper (`faster-whisper`) transcribes audio locally, fully offline once
   the model is cached — `task="translate"` outputs English directly from
   Hindi speech in a single model call.
2. `pyannote.audio` separately determines *who* spoke *when*, purely by
   voice similarity — it has no concept of language or roles.
3. A simple timestamp-overlap alignment step merges the two outputs.
4. A manual filler-word list cleans up transcript noise before metrics are
   computed, since Whisper doesn't reliably strip fillers itself.
5. Whoever has the most total talk time is heuristically labeled "Teacher"
   — an approximation the assignment brief explicitly allows.
6. Engagement metrics (Teacher Dominance Ratio, Student Participation
   Indicator, Interaction Count) are plain arithmetic on the labeled
   transcript — no additional models involved.

## Engagement metrics
| Metric | Formula | Interpretation |
|---|---|---|
| Teacher Dominance Ratio | teacher_talk_time / total_talk_time | High (~0.8+) suggests lecture-style monologue; lower suggests more dialogue |
| Student Participation Indicator | student_talk_time / total_talk_time | Inverse signal to the above — how much room students had to speak |
| Interaction Count | number of speaker switches | Proxy for back-and-forth engagement regardless of time split |

## Assumptions & limitations
- Whisper uses the `small` model by default and translates the Hindi classroom
   recording to English in one pass. Set `WHISPER_MODEL_SIZE` to change this.
- A real short Hindi clip has been processed end to end. The deployed demo has
   also completed transcription, diarization, and report generation on uploaded
   audio.
- Full 40-minute runtime and whole-file metric sanity checks are still a
   release validation step; CPU inference can take several minutes.
- Diarization assumes speaker roles reduce to Teacher vs Student; more than
  2 detected voice clusters are grouped as "Student".
- Teacher/Student assignment is a heuristic: the speaker with the most total
   talk time is labeled Teacher. It should be reviewed for recordings where a
   student speaks most of the time.
- No persistence — each request is processed statelessly.
- Approximate accuracy throughout, per the assignment's stated tolerance.

## Deployment
The demo runs on Hugging Face Spaces with Gradio. Whisper transcription is
placed on the available GPU through `spaces.GPU`; pyannote diarization and
metrics run on CPU. The FastAPI implementation remains available locally for
API testing and exposes `/health`, `/scalar`, and `/api/v1/full-report`.

The deployment pins the Torch, torchaudio, TorchCodec, Gradio, and Hugging Face
Hub versions required by the current Spaces/ZeroGPU environment. A Hugging
Face token must be configured as the `HF_TOKEN` Space secret; never commit it
to `.env` or the repository.

## Long recordings and scaling decision
The current MVP processes an upload as one logical analysis. Hugging Face
ZeroGPU is suitable for the demonstrated short-clip workflow, but a full
40-minute recording can exceed the temporary GPU lease used by transcription.
The live MVP therefore keeps the simple, reliable flow instead of silently
changing the meaning of a long recording.

Chunked processing is intentionally deferred to the separate
`experiment/chunked-processing` branch. A production implementation would need
to split transcription into sequential chunks, preserve absolute timestamps,
write progress and per-chunk logs, and reconcile speaker identities across
chunk boundaries before calculating metrics. Parallel GPU jobs are not assumed
to be available on shared ZeroGPU and could increase failures or memory use.

For longer recordings, the preferred next step is a worker or paid GPU service
with a longer execution lease (for example, RunPod), rather than making the
MVP's speaker analysis approximate. This keeps the submitted demo easy to
understand and leaves scaling as an explicit upgrade path.
