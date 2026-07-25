# 🏡 Real Estate Lead Qualification Voice Agent ("Riya" - Placeholder Realty)

An end-to-end, production-grade Voice AI Agent portfolio project built for a fictional real estate brokerage called **Placeholder Realty**. The agent (**Riya**) receives inbound phone calls via **Twilio Media Streams** or local microphone sessions via a **Browser WebRTC/WebSocket client**, conducts a conversational buyer qualification dialogue, looks up matching inventory from **PostgreSQL**, captures structured lead details, and persists full turn-by-turn transcripts and summaries to a **React + Vite + Tailwind dashboard**.

---

## 🌟 Key Highlights & Architecture

```mermaid
flowchart TD
    subgraph Inbound Audio Channels
        Phone[Phone Caller via PSTN] -->|Twilio Media Streams μ-law| TwilioWS["FastAPI WebSocket (/ws/twilio)"]
        Browser[Browser Microphone User] -->|WebRTC / Audio WebSocket| BrowserWS["FastAPI WebSocket (/ws/browser-audio)"]
    end

    subgraph Pipecat Voice Pipeline
        STT["Deepgram Nova-2 (Streaming STT)"]
        VAD["Silero VAD (Interruption & Barge-in)"]
        LLM["OpenAI GPT-4o (Native Tool Calling)"]
        TTS["ElevenLabs Turbo v2.5 (Streaming TTS)"]
    end

    subgraph Function Calling Tools
        SearchTool["search_properties(location, budget_max, bhk)"]
        LeadTool["save_lead(name, phone, budget, timeline, ...)"]
        EscalateTool["escalate_to_human(reason)"]
    end

    subgraph Storage Layer
        DB[(PostgreSQL / Alembic Migrations)]
        PropsTable[properties table - 22+ Seeded Listings]
        LeadsTable[leads table - Statuses & Criteria]
        ConvsTable[conversations table - Turn Transcripts & Summaries]
    end

    subgraph Frontend
        Dashboard["React 18 + Vite + Tailwind CSS Dashboard"]
    end

    TwilioWS --> STT
    BrowserWS --> STT
    STT --> VAD --> LLM
    LLM --> SearchTool --> PropsTable
    LLM --> LeadTool --> LeadsTable
    LLM --> EscalateTool
    LLM --> TTS
    TTS --> TwilioWS
    TTS --> BrowserWS

    Dashboard -->|REST API| FastAPIApp[FastAPI REST Router]
    FastAPIApp --> LeadsTable
    FastAPIApp --> ConvsTable
    FastAPIApp --> PropsTable
```

---

## 🛠️ Technology Stack

| Component | Technology | Description |
|---|---|---|
| **Backend & Orchestration** | Python 3.12 / FastAPI / Uvicorn | High-performance asynchronous API & WebSocket server |
| **Voice Framework** | Pipecat 1.11.0 | Real-time voice frame orchestration and pipeline runner |
| **Speech-to-Text (STT)** | Deepgram Nova-2 | Streaming transcription with low latency and smart formatting |
| **Text-to-Speech (TTS)** | ElevenLabs Turbo v2.5 | High-fidelity conversational voice synthesis (Rachel / Riya) |
| **LLM Engine** | OpenAI GPT-4o (Native Tools) | Abstracted behind `BaseLLMClient` (swappable for Claude) |
| **Telephony** | Twilio Programmable Voice | WebSocket Media Streams with `TwilioFrameSerializer` |
| **Local Testing Client** | HTML5 / Web Audio API | Live audio waveform visualizer and Web Speech / audio playback |
| **Database & Migrations** | PostgreSQL, SQLAlchemy, Alembic | Async ORM with automatic local SQLite fallback |
| **Frontend Dashboard** | React 18, Vite, Tailwind CSS, Lucide | Filterable leads, turn transcripts, catalog, and embedded tester |
| **Deployment & Containers** | Docker Compose, Railway, Render | Turnkey multi-stage container deployment configs |

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
pip install -r requirements.txt
pip install deepgram-sdk elevenlabs
```

### 4. Database Initialization & Seeding
By default, the backend uses SQLite (`real_estate.db`) for immediate local plug-and-play development without needing Docker. If you have PostgreSQL running, set `DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/real_estate_agent`.

Run the database seed script to generate **22 realistic property listings**:
```bash
python scripts/seed_properties.py
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
3. Riya will greet you: *"Hi there! This is Riya with Placeholder Realty. What kind of property are you looking for today?"*
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

### 3. Twilio Telephony Setup (Real Phone Call)
To connect a real inbound phone number to the agent:
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
4. **Place a Call:** Call your Twilio number from your mobile phone. Twilio will stream the 8kHz audio via WebSocket directly to `/ws/twilio`, connecting you to Riya!

---

## 🛡️ Guardrails & Adversarial Testing

Phase 7 of development executed **10 adversarial failure-mode scenarios** in `tests/test_adversarial_conversations.py` to ensure Riya behaves reliably under edge conditions:

1. **Impatient Caller:** Cuts pleasantries, immediately extracts parameters, and quotes inventory in under 50 words.
2. **Off-Topic Questions:** Acknowledges in 1 brief phrase and gently steers back to real estate qualification.
3. **Legal / Tax Guarantees:** Strict refusal of legal guarantees, redirecting to licensed legal advisors.
4. **Financing Guarantees:** Defers loan interest rate promises to licensed mortgage brokers.
5. **Hallucination Trap:** Requests for non-existent properties return 0 matches; Riya never invents listings.
6. **Caller Silence:** Checks in once after inactivity; gracefully terminates on second silence without looping.
7. **Barge-in / Interruption:** User speech interrupts active playback and resets audio buffers.
8. **Vague Answers:** Uses structured prompts to help buyer narrow budget and timeline.
9. **Hostile Pushback:** Maintains professional composure, de-escalates, and offers human broker transfer.
10. **Immediate Human Escalation:** Triggers `escalate_to_human()` and marks lead as escalated.

Run the complete test suite:
```bash
pytest -v
```
*(All 19 tests will pass in ~1.0s).*

See [NOTES.md](file:///c:/Users/jaish/Desktop/NEWPROJECT/NOTES.md) for detailed Before & After failure logs and engineering decisions.

---

## ☁️ Deployment

### Deploying to Railway
1. Push your repository to GitHub.
2. Link the repository on [Railway](https://railway.app/).
3. Add a **PostgreSQL** service on Railway.
4. Add the environment variables from `.env.example` in Railway's Variables tab.
5. Railway uses `railway.json` and `Dockerfile` to build and deploy automatically.
6. Set your Twilio Voice Webhook URL to: `https://your-railway-app.up.railway.app/api/twilio/incoming-call`.

### Deploying to Render
1. Create a new **Web Service** on [Render](https://render.com/) pointing to your repository.
2. Use the provided [render.yaml](file:///c:/Users/jaish/Desktop/NEWPROJECT/render.yaml) blueprint to spin up the web app and managed PostgreSQL instance simultaneously.

---

## 📄 License
MIT License. Built for portfolio demonstration of Voice AI agent orchestration, Pipecat, and LLM tool calling.
