# UPDATES LOG

> This file is the project's persistent memory across agent sessions. An
> agentic IDE's own context does NOT carry over between runs — this file is
> how the next session knows what already happened. Rules:
> 1. Read this whole file first, before starting any new work.
> 2. Never overwrite past entries — only append a new one at the bottom.
> 3. Every entry should cover: what was done, what was decided (and why),
>    what's currently blocked/unresolved, and what the next session should
>    start with.
> 4. Cross-check `TASKS.md` and update its checkboxes to match reality before
>    ending the session.

---

## 2026-09-05 — Planning & scaffold session
**Done:**
- Reviewed MakerGhat pre-work brief, deadline confirmed as Sept 8, 2026
- Decided architecture: FastAPI (not NestJS) for Task 1, since the whole
  pipeline is Python-native ML tooling
- Confirmed sample audio: Hindi, ~40 minutes total
- Built full project scaffold: `app/` package with transcribe, diarize,
  align, filters, roles, metrics modules, wired together in `main.py`
  behind a single `/api/v1/full-report` endpoint
- Added Scalar API docs at `/scalar`
- Created `TASKS.md` and this `UPDATES.md` as persistent tracking

**Decisions made:**
- Whisper `task="translate"` used to get English transcript output directly
  from Hindi audio (single model call, no separate translation step)
- Teacher/Student role heuristic: whoever has more total talk time = Teacher
  (brief explicitly allows approximation here)
- Filler words handled via a manual strip list in `filters.py` — Whisper does
  NOT reliably filter these itself
- No persistence/DB for MVP — stateless request/response only
- Planned deployment target: Hugging Face Spaces (Docker SDK) — free tier
  RAM is much more suitable for Whisper+pyannote than Render/Railway's 512MB

**Blocked / not yet done:**
- HF token not yet generated/added to `.env`
- Pipeline not yet run against any real audio (short clip or full file)
- Demo interface not started
- Dockerfile for deployment not started

**Next session should start with:**
- Phase 0 remaining items in `TASKS.md` (HF token + access), then Phase 1
  (short clip validation) before touching the full 40-min file

---

## 2026-09-05 (later) — Environment fixes + short-clip validation
**Done:**
- Fixed a chain of version-compat breaks: pinned `torch==2.5.1`,
  `torchaudio==2.5.1` (newer torchaudio removed `AudioMetaData` that
  pyannote.audio still references), `huggingface_hub<1.0` (v1.0 removed
  `use_auth_token` that this pyannote.audio version still calls
  internally), and made `diarize.py` try both `token=` and
  `use_auth_token=` params so it works across pyannote.audio versions
- Ran full pipeline successfully on a real 2-minute Hindi clip cut from
  the actual assignment audio — end to end, no crashes
- Verified clip duration (120s) matches pipeline's reported duration
  (120.2s) via ffprobe — sanity check passed
- Wrote `CODE_WALKTHROUGH.md` — full architecture/design-decision doc for
  interview/review readiness

**Decisions made / findings:**
- Result on the test clip: `{'SPEAKER_00': 'Teacher', 'UNKNOWN': 'Student'}`
  — flagged that `UNKNOWN` in `align.py` means "no matching speaker turn
  found," not necessarily a confirmed second speaker. Needs one diagnostic
  check (print distinct speaker labels from `diarize_audio()` output)
  before trusting this specific run's Teacher/Student split as ground truth

**Blocked / not yet done:**
- Diagnostic check above not yet run — unclear if this clip has 1 or 2
  real speakers
- Full 40-min file not yet run
- Demo interface not started
- Dockerfile / deployment not started
- README assumptions section not yet filled with real values

**Next session should start with:**
- Run the one-line diagnostic (`set(t["speaker"] for t in turns)`) to
  confirm speaker count on the test clip
- Then run the full 40-min file
- Then build the demo interface (Phase 4 in TASKS.md)

---

## 2026-09-06 — Full-file CPU run still in progress; API/demo scaffolding ready
**Done:**
- Confirmed the real 40-minute file lasts about 4062s (`ffprobe`), so the
  long inference run is expected rather than a sign of a hung pipeline
- Started the full-file validation through the project venv using the same
  `tests.test_pipeline_manual` path used for the short clip, and the log shows
  it reaches the "Transcribing..." stage without crashing early
- Added the local FastAPI demo page and the HF Dockerfile entry points, so the
  remaining HTTP and deployment work is prepared around the final validated
  output
- Added a project `.gitignore` to keep `.env` and virtualenv state out of the
  repo, matching the requirement that the real HF token must never be tracked

**Decisions made / findings:**
- The CPU-based full-file run is slower than the short clip and may take many
  minutes; this is a real runtime cost of Whisper + pyannote on a 40-minute
  recording, not an app bug
- The API and demo scaffolding are ready, but the actual full-endpoint
  verification must wait until the full-file output completes and the final
  transcript/metrics are available for a real regression check

**Blocked / not yet done:**
- Phase 2 final metrics and transcript sanity checks are still pending because
  the 40-minute run has not yet completed
- Phase 3 API verification, Phase 4 demo validation, and the README/PRD final
  write-up remain queued behind the above runtime completion

**Next session should start with:**
- Let the current full-file run complete and capture its final transcript and
  metric output from the log or console
- Then validate `/health`, `/scalar`, and `/api/v1/full-report` against the
  real file and the actual HTTP wrappers
- Then finish the README/PRD assumptions and deployable Docker handoff

## 2026-09-06 — CPU diarization baseline and deployment portability
**Done:**
- Decided to keep pyannote diarization on CPU for the baseline. Moving the
  pipeline to CUDA failed locally with a Windows cuDNN symbol error, while a
  basic Torch CUDA convolution succeeded; this isolates the issue to the
  pyannote/cuDNN path rather than the GPU itself.
- Updated Whisper to select CUDA automatically when available and CPU
  otherwise, so the Docker/Hugging Face runtime does not require a GPU.
- Replaced the Linux-only `/tmp` upload path with `tempfile.NamedTemporaryFile`,
  making the full-report endpoint portable on Windows and Linux.
- Verified the application modules compile and confirmed `/`, `/health`,
  `/scalar`, and `/demo` all return HTTP 200 locally.
- Confirmed Docker is installed locally (`28.4.0`).

**Decisions made:**
- Use GPU Whisper plus CPU pyannote locally for now; revisit GPU diarization
  after deployment and baseline validation.
- Do not claim full-report success until an actual upload completes, because
  that path runs both ML models and is substantially slower than route checks.

**Blocked / not yet done:**
- Full 40-minute validation still has no final metrics in this session.
- Full multipart `/api/v1/full-report` test, Docker image build, HF Spaces
  deployment, and live end-to-end verification remain open.
- Local Docker build is currently blocked because Docker Desktop's Linux
  engine is not running (`dockerDesktopLinuxEngine` pipe unavailable).

**Next session should start with:**
- Build the Docker image and fix any dependency/container issues.
- Upload `short_clip.wav` through `/api/v1/full-report` locally and inspect the
  returned transcript, roles, and metrics.
- Deploy the verified image to Hugging Face Spaces, then run the same short-clip
  request against the live URL before attempting the full recording.

## 2026-09-06 — Local CPU deployment image verified
**Done:**
- Built the Docker image successfully after Docker Desktop was started.
- Fixed the Dockerfile so it installs CPU-only `torch==2.5.1+cpu` and
  `torchaudio==2.5.1+cpu`; the general requirements install no longer replaces
  them with CUDA packages.
- Verified inside the image: Torch `2.5.1+cpu`, CUDA unavailable, and the
  FastAPI application imports successfully.
- Started the final image as a container on port 7860; `/health` returned 200
  and the container remained running.

**Blocked / not yet done:**
- Hugging Face Space deployment and live short-clip end-to-end upload remain.
- Full-report inference is intentionally not run during container smoke tests;
  it would load the Whisper and pyannote models and take substantially longer.

**Next session should start with:**
- Push this repository to the Hugging Face Docker Space or configure the Space
  to build from the repository.
- Add `HF_TOKEN` as a Space secret, wait for the build, and test `/health`.
- Upload `short_clip.wav` to `/api/v1/full-report` on the live URL.

## 2026-09-06 — Fixed blocking demo requests
**Done:**
- Diagnosed repeated `GET /demo?audio_file=short_clip.wav` entries as the
  browser's default form submission after the JavaScript handler was missed.
- Added explicit `method="post"`, `/api/v1/full-report` action, and multipart
  encoding to the demo form.
- Changed `full_report` from `async def` to a synchronous FastAPI handler so
  blocking Whisper and pyannote inference runs in FastAPI's worker thread
  instead of freezing the Uvicorn event loop and making the tab appear stuck.
- Rebuilt and restarted the container; direct checks confirmed `/health` 200
  and the corrected multipart form served at `/demo`.

**Next session should start with:**
- Refresh `http://localhost:7860/demo` with Ctrl+F5 and upload the short clip.
- Confirm the container log shows `POST /api/v1/full-report` and wait for the
  analysis response before testing the full recording.

## 2026-09-06 — Prevented stale demo page caching
**Done:**
- Diagnosed the apparent no-op submit as a stale/cached demo document combined
  with the old default GET form behavior; the container was idle and `/health`
  remained responsive.
- Added `Cache-Control: no-store` and `Pragma: no-cache` headers to `/demo`.
- Rebuilt and restarted the container. Verified the fresh response contains the
  explicit POST multipart form and returns the no-cache headers.