# TASKS — Classroom Voice Analytics MVP

> **Agent instructions:** Before starting work in a new session, read `UPDATES.md`
> first — it holds what happened in prior sessions, since your own context does
> not persist between runs. After finishing work in this session, check off
> completed items below AND append a new dated entry to `UPDATES.md` before
> ending your turn. Never skip the UPDATES.md append — it's the only memory
> that survives across sessions.

## Phase 0 — Setup
- [x] Project scaffold created (app/, tests/, requirements.txt, .env.example)
- [x] Dependencies installed (`pip install -r requirements.txt`)
- [x] Hugging Face token generated, added to `.env`
- [x] Access accepted on `pyannote/speaker-diarization-3.1` and `pyannote/segmentation-3.0`

## Phase 1 — Short-clip validation (do this before touching the full 40-min file)
- [x] Cut a 2-3 min test clip from the full recording (ffmpeg)
- [x] Run `python -m tests.test_pipeline_manual <short_clip>`
- [x] Confirm: transcript looks reasonable, speakers get separated, roles assigned sensibly — confirmed on the locally validated short clip; full-file speaker diagnostic is still being treated as a live check on the 40-minute recording
- [x] Note actual runtime for the short clip (used to estimate full-file runtime)

## Phase 2 — Full pipeline on real audio
- [ ] Run full 40-min recording through the same test script (expect longer runtime — see PRD §6)
  Status: started on the real file and still running in the background on CPU; it has not yet produced the final metrics, so Phase 2 remains open
- [ ] Sanity-check teacher/student heuristic held up across the whole file
- [ ] Sanity-check filler-word list catches what actually shows up in this transcript (extend list if needed)

## Phase 3 — API
- [ ] `app/main.py` full-report endpoint tested via Scalar UI (`/scalar`)
- [ ] CORS confirmed working if demo UI is a separate frontend

## Phase 4 — Demo interface
- [ ] Simple page/Streamlit app built showing: transcript, metrics, summary
- [ ] Interface calls `/api/v1/full-report` and renders the response

## Phase 5 — Deployment
- [ ] Dockerfile written for HF Spaces (Docker SDK)
- [ ] Deployed, live URL confirmed working end-to-end (not just health check)

## Phase 6 — Documentation & submission
- [ ] README.md filled in (structure, approach, assumptions — see README skeleton)
- [ ] PRD.md assumptions section filled in with final values (model size used, language handling decision, etc.)
- [ ] GitHub repo pushed, public
- [ ] Live demo link tested from a fresh browser/incognito window