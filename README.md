# 🏡 EstateStream AI: Voice Agent Prototype for Real Estate
> **Tech Stack:** Python, FastAPI, OpenAI GPT-4o, ElevenLabs, React, PostgreSQL, Docker

A voice agent prototype for real estate lead qualification (**EstateStream AI**). The agent (**Riya**) conducts conversational buyer qualification through a browser microphone interface using the browser Web Speech API, searches verified listings from the database (22 seeded listings), uses OpenAI GPT-4o function calling (`search_properties`, `save_lead`, `escalate_to_human`), synthesizes voice responses using ElevenLabs REST (with browser speechSynthesis fallback), and persists turn transcripts to a React dashboard. Phone calls run through a server-side pipeline (voice activity detection, Whisper/Deepgram STT, Piper/ElevenLabs TTS, barge-in) on the Twilio Media Streams protocol, testable for free with the built-in phone simulator.

---

## 🌟 Key Highlights & Architecture

```mermaid
flowchart TD
    subgraph Inbound Channels
        Browser[Browser User Microphone] -->|Browser Web Speech STT| BrowserWS["FastAPI WebSocket (/ws/browser-audio)"]
        Phone[Phone Caller via PSTN] -->|Twilio Incoming Call Webhook| TwilioHook["FastAPI Twilio Endpoint (/api/twilio/incoming-call)"]
    end

    subgraph Voice & LLM Pipeline
        BrowserWS -->|Text Turn| LLM["OpenAI GPT-4o (Function Calling)"]
        LLM -->|Text Response| TTS["ElevenLabs REST / Browser SpeechSynthesis Fallback"]
        TTS -->|Audio Playback| BrowserWS
    end

    subgraph Function Calling Tools
        SearchTool["search_properties(location, budget_max, bhk)"]
        LeadTool["save_lead(name, phone, budget, timeline, ...)"]
        EscalateTool["escalate_to_human(reason)"]
    end

    subgraph Storage Layer
        DB[(PostgreSQL / SQLite Fallback)]
        PropsTable[properties table: 22 Seeded Listings]
        LeadsTable[leads table: Statuses & Criteria]
        ConvsTable[conversations table: Turn Transcripts & Summaries]
    end

    subgraph Frontend
        Dashboard["React 18 + Vite + Tailwind CSS Dashboard"]
    end

    LLM --> SearchTool --> PropsTable
    LLM --> LeadTool --> LeadsTable
    LLM --> EscalateTool

    Dashboard -->|REST API| FastAPIApp[FastAPI REST Router]
    FastAPIApp --> LeadsTable
    FastAPIApp --> ConvsTable
    FastAPIApp --> PropsTable
```

---

## 🛠️ Technology Stack

| Component | Technology | Description |
|---|---|---|
| **Backend & Orchestration** | Python 3.12 / FastAPI / Uvicorn | Asynchronous API & WebSocket server |
| **Speech-to-Text (STT)** | Browser Web Speech API | Client-side speech recognition in the live flow (Deepgram REST helper exists in backend but is not used in the live browser flow) |
| **Text-to-Speech (TTS)** | ElevenLabs REST | Conversational voice synthesis via ElevenLabs REST API with browser speechSynthesis fallback |
| **LLM Engine** | OpenAI GPT-4o (Function Calling) | Abstracted behind `BaseLLMClient` with tools (`search_properties`, `save_lead`, `escalate_to_human`) and offline `MockLLMClient` fallback |
| **Telephony** | Twilio Media Streams protocol | Full server-side phone pipeline on `/ws/twilio`: 8 kHz μ-law, voice activity detection, STT, agent, TTS, barge-in (`clear`), silence hang-up. Free browser simulator at `/phone-sim` |
| **Phone STT / TTS** | faster-whisper + Piper (free, local) or Deepgram + ElevenLabs | Pluggable via `STT_ENGINE` / `TTS_ENGINE`; `auto` uses hosted engines when keys are set |
| **Voice Framework** | Pipecat (Planned / Not Implemented) | Standalone experimental pipeline file in repository, not wired into active server |
| **Local Testing Client** | HTML5 / Web Audio API | Live audio waveform visualizer and browser voice session testing |
| **Database & Migrations** | PostgreSQL, SQLAlchemy, Alembic | Async ORM with automatic local SQLite fallback and 22 seeded listings |
| **Frontend Dashboard** | React 18, Vite, Tailwind CSS, Lucide | Filterable leads, turn transcripts, catalog, and embedded tester |
| **Deployment & Containers** | Docker Compose, Railway, Render | Multi-stage container deployment configs |

---

## 📁 Repository Structure

```
├── backend/
│   ├── main.py                  # FastAPI application entry point, CORS, routers
│   ├── config.py                # Pydantic v2 settings loading from .env
│   ├── database.py              # Async & sync SQLAlchemy engine and session providers
│   ├── models.py                # Property, Lead, and Conversation ORM models
│   ├── schemas.py               # Pydantic request/response schemas
│   ├── routers/
│   │   ├── properties.py        # Property catalog queries and search
│   │   ├── leads.py             # Lead management, status updates, filtering
│   │   ├── conversations.py     # Conversation logs and transcripts
│   │   ├── chat.py              # Text chat endpoint for agent testing
│   │   └── voice.py             # Twilio TwiML, Twilio Media Stream WS, Browser Audio WS
│   ├── services/
│   │   ├── property_service.py  # Property lookup and strict match filters
│   │   ├── lead_service.py      # Lead upsert and status lifecycle
│   │   └── conversation_service.py # Post-call AI summarization and transcript logging
│   └── static/
│       └── browser_client.html  # Standalone browser mic tester with visualizer
├── voice/
│   ├── agent.py                 # AgentSession conversation loop & tool dispatcher
│   ├── prompts.py               # Riya persona, guardrails, and tool specifications
│   ├── llm_client.py            # BaseLLMClient, OpenAILLMClient & MockLLMClient
│   ├── audio_services.py        # Deepgram STT & ElevenLabs TTS client wrappers
│   └── pipeline.py              # Pipecat framework pipeline builder
├── dashboard/                   # React + Vite + Tailwind CSS frontend
│   ├── src/
│   │   ├── App.jsx              # Main tab coordinator and modal container
│   │   ├── api.js               # REST client for backend endpoints
│   │   └── components/
│   │       ├── Navbar.jsx       # Header with status pills and tester trigger
│   │       ├── LeadList.jsx     # Filterable leads table and qualification cards
│   │       ├── LeadDetailModal.jsx # Full turn transcript and AI summary viewer
│   │       ├── PropertyCatalog.jsx # 22+ seeded listings search view
│   │       ├── ConversationsView.jsx # Call session logs viewer
│   │       └── VoiceTestModal.jsx # Embedded microphone testing modal
├── alembic/                     # Alembic database migration scripts
├── scripts/
│   ├── seed_properties.py       # Seeds 22+ realistic property listings
│   └── cli_chat.py              # Terminal interactive chat with Riya
├── tests/
│   ├── test_agent_tools.py      # Agent tool invocation and persistence tests
│   ├── test_api.py              # FastAPI endpoint integration tests
│   └── test_adversarial_conversations.py # 10 failure-mode guardrail test suites
├── Dockerfile                   # Multi-stage production build
├── docker-compose.yml           # PostgreSQL + Backend container orchestration
├── .env.example                 # Fully commented environment variable template
├── NOTES.md                     # Engineering assumptions & Phase 7 test results
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.11 or 3.12
- Node.js v18+ and npm
- (Optional) Docker Desktop if testing PostgreSQL in containers

### 2. Environment Setup
Clone the repository and copy the environment template:
```bash
cp .env.example .env
```
Populate your API keys in `.env`:
```env
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```
*(Note: If you do not have active API credits, the application includes an intelligent heuristic fallback client that allows testing the text agent, function calling, property search, and dashboard 100% offline without errors).*

### 3. Install Python Dependencies
```bash
pip install -r requirements-dev.txt   # app + test deps (use requirements.txt for production)
```

### 4. Database Initialization & Seeding
By default, the backend uses SQLite (`real_estate.db`) for immediate local plug-and-play development without needing Docker. If you have PostgreSQL running, set `DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/real_estate_agent`.

The backend seeds **22 property listings** plus demo leads automatically on first start (only when the tables are empty). To wipe and reseed manually:
```bash
python scripts/seed_properties.py --reset
```
To apply Alembic migrations:
```bash
alembic upgrade head
```

---

## 🖥️ Running the Application

### Option A: Run Backend & Dashboard Locally

**1. Start the FastAPI Backend Server:**
```bash
uvicorn backend.main:app --reload --port 8000
```
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Standalone Browser Mic Tester: [http://localhost:8000/voice-test](http://localhost:8000/voice-test)

**2. Start the React Frontend Dashboard:**
```bash
cd dashboard
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

### Option B: Run with Docker Compose

To run PostgreSQL and the containerized backend with frontend assets bundled:
```bash
docker compose up --build
```
The application will boot on `http://localhost:8000`.

---

## 🎙️ Testing the Voice Agent

### 1. Browser Microphone Flow (Zero External Setup)
1. Open the React Dashboard at `http://localhost:5173` and click **"Live Mic Tester"** in the top right (or visit `http://localhost:8000/voice-test`).
2. Click **"Start Voice Call"** and grant microphone permissions.
3. Riya will greet you: *"Hi there! This is Riya with EstateStream AI. What kind of property are you looking for today?"*
4. Speak naturally:
   - *"I'm looking for a 3 BHK in Downtown with a budget of $800,000."*
   - Watch the agent invoke `search_properties()`, locate a real listing from PostgreSQL, and describe it.
   - Supply your name and timeline: *"My name is Alex Chen, planning to move in 3 months."*
   - Riya triggers `save_lead()`.
5. Click **"End Call"**: A structured post-call summary is generated, saved to the database, and immediately appears in the dashboard!

### 2. Terminal CLI Chat Mode
To test the conversation logic without audio:
```bash
python scripts/cli_chat.py
```

### 3. Live Phone Calls, Free (Phone Simulator)

The phone pipeline runs entirely on the server, exactly as it would for a real Twilio call:

```
caller audio (8 kHz μ-law, 20 ms frames) → voice activity detection → speech-to-text
  → Riya (LLM + tools) → text-to-speech (8 kHz μ-law) → back on the line
  + barge-in: caller talks over Riya → server sends Twilio `clear` → playback stops
  + silence: no speech for 8 s → check-in; again → goodbye → hang-up
```

No Twilio account or API keys needed:
```bash
pip install -r requirements-voice.txt        # Whisper + Piper (free, run on CPU)
uvicorn backend.main:app --port 8000          # first start downloads ~200 MB of models
```
Open **http://localhost:8000/phone-sim** (or "Phone Call" in the dashboard), use headphones, press **Call Riya**.
The simulator is a browser phone that speaks the exact Twilio Media Streams protocol to `/ws/twilio`,
so the same server code answers real Twilio calls unchanged. It also shows live transcripts, tool calls and per-turn latency.

Measured on a laptop-class CPU with the offline agent: speech-to-text ≈ 0.9–1.1 s, reply on the line ≈ 1.9 s after the
caller's 0.7 s end-of-speech pause. GPT-4o adds roughly 0.5–1.5 s per turn.

### 4. Real Twilio Telephony (Optional, Paid After Trial)
To test the inbound call greeting with a phone number:
1. **Expose your local server** using [ngrok](https://ngrok.com/):
   ```bash
   ngrok http 8000
   ```
   Copy the HTTPS forwarding URL (e.g. `https://abc123.ngrok-free.app`).
2. **Set the public URL** in `.env`:
   ```env
   PUBLIC_BASE_URL=https://abc123.ngrok-free.app
   ```
3. **Configure Twilio Console:**
   - Log in to your [Twilio Console](https://console.twilio.com/) and navigate to **Phone Numbers** &rarr; **Manage** &rarr; **Active Numbers**.
   - Select your Twilio phone number.
   - Under **Voice Configuration** &rarr; **A Call Comes In**:
     - Select **Webhook**
     - Set URL to: `https://abc123.ngrok-free.app/api/twilio/incoming-call`
     - Set HTTP method to **HTTP POST**
   - Click **Save**.
4. **Place a Call:** Call your Twilio number. Riya greets you and holds the full conversation through `/ws/twilio`; the caller's number is saved as the lead's phone.
   Twilio's trial (no card) includes limited voice and Media Streams minutes and restricts calls to your sign-up country, so the simulator above is the free way to test.

---

## 🛡️ Guardrails & Adversarial Testing

Phase 7 of development executed **10 adversarial failure mode scenarios** (out of 28 automated tests total in the repository). All 28 tests run against a rule based mock LLM (`MockLLMClient`) to ensure reproducible evaluation without live API keys or latency:

1. **Impatient Caller:** Cuts pleasantries, immediately extracts parameters, and quotes inventory in under 50 words.
2. **Off-Topic Questions:** Acknowledges in 1 brief phrase and gently steers back to real estate qualification.
3. **Legal / Tax Guarantees:** Strict refusal of legal guarantees, redirecting to licensed legal advisors.
4. **Financing Guarantees:** Defers loan interest rate promises to licensed mortgage brokers.
5. **Hallucination Trap:** Requests for non existent properties return 0 matches from the database (22 seeded listings); Riya never invents listings.
6. **Caller Silence:** Checks in once after inactivity; gracefully terminates on second silence without looping.
7. **Barge-in / Interruption:** Client side speech interruption stops playback and resets turn state.
8. **Vague Answers:** Uses structured prompts to help buyer narrow budget and timeline.
9. **Hostile Pushback:** Maintains professional composure, de-escalates, and offers human broker transfer.
10. **Immediate Human Escalation:** Triggers `escalate_to_human()` and marks lead as escalated.

Run the complete test suite:
```bash
pytest -v
```
*(All 28 tests run against the rule based mock LLM on a throwaway SQLite file, so your local `real_estate.db` is never touched. 9 of them are end-to-end regression tests over the real `/ws/browser-audio` WebSocket; see `DEBUG_REPORT.md`.)*

See [NOTES.md](NOTES.md) for detailed Before & After failure logs and engineering decisions.

---

## ☁️ Deployment

### Deploying to Railway
1. Push your repository to GitHub.
2. Link the repository on [Railway](https://railway.app/).
3. Add a **PostgreSQL** service on Railway.
4. Add the environment variables from `.env.example` in Railway's Variables tab.
5. Railway uses `railway.json` and `Dockerfile` to build and deploy automatically. The container binds to Railway's `$PORT`.
   The React dashboard is served by the backend at `/dashboard` (same origin, no extra config).
6. Set your Twilio Voice Webhook URL to: `https://your-railway-app.up.railway.app/api/twilio/incoming-call`.

### Deploying to Render
1. Create a new **Web Service** on [Render](https://render.com/) pointing to your repository.
2. Use the provided [render.yaml](render.yaml) blueprint. Note: it uses SQLite, and Render's free-tier disk is ephemeral, so leads are lost on every redeploy or spin-down. Point `DATABASE_URL`/`DATABASE_URL_SYNC` at a managed PostgreSQL instance for anything you want to keep.

### Split deploy (frontend on Vercel)
Build the dashboard with `VITE_API_URL=https://<your-backend>` and add the Vercel origin to the backend's `CORS_ORIGINS`. Without `VITE_API_URL` the dashboard calls its own origin.

---

## 📄 License
MIT License. Built for portfolio demonstration of voice agent lead qualification and LLM function calling.
