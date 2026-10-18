import logging
import os
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database import init_db
from backend.routers import properties, leads, conversations, chat, voice


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown routines."""
    # Ensure database tables exist upon startup
    await init_db()
    if settings.PHONE_PRELOAD_MODELS:
        # Load STT/TTS models in the background so the first phone call doesn't stall.
        import asyncio
        from voice.telephony.engines import warm_up
        asyncio.create_task(warm_up())
    yield


app = FastAPI(
    title="EstateStream AI: Voice Agent Prototype for Real Estate",
    description="Backend API and Voice Services for Riya, Voice Agent Prototype for Real Estate Lead Qualification",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
# Wildcard origins only outside production. (Credentials can't be combined with "*".)
_allow_any = settings.DEBUG and settings.ENVIRONMENT != "production"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_any else origins,
    allow_credentials=not _allow_any,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(properties.router)
app.include_router(leads.router)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(voice.router)

# Mount static folder for browser voice client
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# The Vite build references its bundle as /assets/*.js, so it must be served from /assets
# (previously /dashboard loaded a blank page because every asset 404'd).
dashboard_assets = os.path.join(static_dir, "dashboard", "assets")
if os.path.isdir(dashboard_assets):
    app.mount("/assets", StaticFiles(directory=dashboard_assets), name="dashboard-assets")


@app.get("/voice-test", response_class=HTMLResponse)
async def voice_test_page():
    """Serves the standalone browser microphone voice tester page."""
    html_path = os.path.join(static_dir, "browser_client.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return HTMLResponse("<h1>Browser client not found</h1>", status_code=404)


@app.get("/phone-sim", response_class=HTMLResponse)
async def phone_simulator_page():
    """Free phone simulator: speaks the Twilio Media Streams protocol from the browser."""
    html_path = os.path.join(static_dir, "phone_simulator.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return HTMLResponse("<h1>Phone simulator not found</h1>", status_code=404)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Serves the React dashboard when running unified server."""
    dash_html = os.path.join(static_dir, "dashboard", "index.html")
    if os.path.exists(dash_html):
        return FileResponse(dash_html)
    return HTMLResponse("<h1>Dashboard build not found. Run 'npm run build' in dashboard/</h1>", status_code=404)


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestrators (Railway / Render)."""
    return {
        "status": "healthy",
        "agent": "Riya",
        "project": "EstateStream AI",
        "title": "Voice Agent Prototype for Real Estate",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
async def root():
    return {
        "message": "Welcome to EstateStream AI Voice Agent Prototype API",
        "docs": "/docs",
        "voice_test_client": "/voice-test",
        "phone_simulator": "/phone-sim",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
