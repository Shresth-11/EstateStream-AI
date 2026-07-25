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
    build-essential \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir deepgram-sdk elevenlabs

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
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run database migrations and start server
CMD ["sh", "-c", "alembic upgrade head && python scripts/seed_properties.py && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
