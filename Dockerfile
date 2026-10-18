# Multi-stage Dockerfile for Real Estate Lead Qualification Voice Agent

# --- Stage 1: Build React Dashboard ---
FROM node:22-alpine AS frontend-builder
WORKDIR /app/dashboard
COPY dashboard/package*.json ./
RUN npm install
COPY dashboard/ ./
RUN npm run build

# --- Stage 2: Python Backend & Serving ---
FROM python:3.12-slim AS runner

WORKDIR /app

# Install system audio dependencies and build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
# LOCAL_VOICE=true also installs free local speech engines (Whisper + Piper, ~400 MB image growth)
# for the phone pipeline. Leave false if you use Deepgram + ElevenLabs keys instead.
ARG LOCAL_VOICE=false
COPY requirements.txt requirements-voice.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    if [ "$LOCAL_VOICE" = "true" ]; then pip install --no-cache-dir -r requirements-voice.txt; fi
ENV MODELS_DIR=/app/models

# Copy backend application and voice modules
COPY backend/ ./backend/
COPY voice/ ./voice/
COPY scripts/ ./scripts/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY pytest.ini .
COPY .env.example .

# Copy built frontend assets into backend static folder
COPY --from=frontend-builder /app/dashboard/dist ./backend/static/dashboard

EXPOSE 8000

ENV HOST=0.0.0.0
ENV PORT=8000
ENV ENVIRONMENT=production

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run database migrations and start server
# Migrations only. Demo data is seeded by the app on startup *only if tables are empty*.
# (The old CMD ran seed_properties.py, which wipes all leads/conversations on every restart.)
# Railway/Render inject $PORT; fall back to 8000 locally.
CMD ["sh", "-c", "alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
