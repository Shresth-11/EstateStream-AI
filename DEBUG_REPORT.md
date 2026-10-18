# Debugging Pass: What Was Broken and What Changed

The original 19 tests all passed, but none of them exercised the live WebSocket, the dashboard build, or multi-call behaviour. An end-to-end probe against the running server found the bugs below. Each fix has a regression test in `tests/test_regressions.py` (28 tests total, all passing).

## Critical (feature visibly broken)

| # | Symptom | Root cause | Fix |
|---|---|---|---|
| 1 | Conversations tab showed only demo data | Seed data uses outcome `not_interested`, missing from the `ConversationOutcome` enum, so `GET /api/conversations` returned **500** | Added `NOT_INTERESTED`; `normalize_outcome()` coerces any LLM-supplied outcome into a valid value |
| 2 | Dashboard looked fine even when the backend was broken | `api.js` silently swapped in hardcoded leads/conversations on any error *or empty result*; `updateLeadStatus` faked success | Fallback is now opt-in (`VITE_DEMO_FALLBACK=true`); real errors show a red banner; status changes roll back on failure |
| 3 | Blank page at `/dashboard` (Docker / Railway / Render) | Vite build references `/assets/*.js`, which was never mounted | `/assets` mounted in `backend/main.py` |
| 4 | Deployed dashboard talked to the wrong server | Any non-localhost host defaulted to a hardcoded, stale Render URL | Same-origin by default; `VITE_API_URL` for split deploys |
| 5 | Every voice call overwrote the same lead | Browser sessions all used the hardcoded phone `+15559876543`; `save_lead` upserts by phone | No fake caller identity; phone resolves caller-stated, then caller ID, then this session's lead, then `unknown-<session>` |
| 6 | **All leads and calls wiped on every container restart** | Docker `CMD` ran `seed_properties.py`, which defaulted to `reset=True` | Removed from `CMD` (the app seeds only empty tables); script now needs `--reset` explicitly |
| 7 | Mic stopped listening after the first pause | `recognition.onend` read stale React state (`inCall` was always `false`), so it never restarted | Refs for long-lived callbacks |
| 8 | Silence handling never fired in the live app | Empty turns were dropped server-side, and the client never sent silence | Client sends a silence turn after 9s idle; server treats empty text as `[silence]` |
| 9 | Every call tagged "qualified" (or "escalated") | Heuristic summary matched Riya's own words ("looking for", "advisor"), and the summarizer's outcome overrode the hard session facts | Outcome precedence: escalated, then no speech (`dropped`), then lead saved (`qualified`), then summarizer. The heuristic reads caller turns only |
| 10 | One OpenAI hiccup killed the whole call | No exception handling around LLM/tool calls; the error bubbled up and closed the WebSocket | LLM and tool errors produce a spoken recovery line; DB session is rolled back on tool failure |

## Functional bugs

- **Agent loop.** It could return an empty reply after four back-to-back tool calls. The final iteration now withholds tools, and an empty reply gets a fallback.
- **OpenAI payload.** Tool messages carried an internal `name` key, which is now stripped before sending. Client has a 20s timeout and 2 retries.
- **Mock LLM (offline mode) parsing:**
  - `$450k` was parsed as 50k.
  - `$1.5 million 2 BHK` was parsed as 1 BHK.
  - A phone number triggered a property search instead of `save_lead`.
  - Every saved lead was "John Doe".
  - Now uses regex parsers for BHK, budget, phone, name and timeline. The mock carries earlier criteria into `save_lead`.
- **Lead status.** A later partial save could downgrade a qualified lead. Status is now derived from the merged fields. Phones are normalized, so `98765-43210` and `9876543210` are the same lead.
- **Barge-in.** It only triggered after a full sentence. Interim results now stop playback, and an echo filter stops Riya interrupting or answering her own voice through laptop speakers.
- **Audio.** `AudioContext` was never resumed or closed, which leaked contexts and left playback suspended on some browsers. Cartesia returned raw PCM that the browser can't decode; it now requests MP3.
- **Twilio:**
  - The call sent MP3 bytes as Twilio media, which needs 8 kHz mu-law and so played noise. That send is removed.
  - The caller's number is now passed through as a `<Parameter>`.
  - The "Placeholder Realty" branding is gone.
  - `python-multipart` is added; it was missing, so form parsing failed.
- **Tests.** They wrote into your real `real_estate.db`. `tests/conftest.py` now uses a temp DB and forces mock mode.

## Deployment / config

- **Port.** The container hardcoded 8000. It now binds `${PORT:-8000}` for Railway and Render.
- **CORS.** It was `*` with credentials even in production. Wildcard is now only allowed outside production.
- **Image size.** Dropped unused heavy deps: `pipecat-ai`, `deepgram-sdk`, `elevenlabs`, `twilio`, `ffmpeg`, `build-essential`. The code uses plain `httpx`. Test deps moved to `requirements-dev.txt`.
- **Render.** `render.yaml` uses SQLite on an ephemeral disk, so data is lost on redeploy. This is documented; use Postgres for anything persistent.

## Still out of scope (unchanged, documented as before)

- Twilio caller audio is not processed (the stub is unchanged).
- `voice/pipeline.py` is dead code.
- There is no authentication on the API or WebSockets.
