import os
from contextlib import asynccontextmanager
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
    yield


app = FastAPI(
    title="EstateStream AI — Real-Time Voice AI Agent for Real-Estate Sales",
    description="Backend API and Voice Pipeline for Riya, Real-Time Voice AI Agent for Real-Estate Sales",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins + ["*"] if settings.DEBUG else origins,
    allow_credentials=True,
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


@app.get("/voice-test", response_class=HTMLResponse)
async def voice_test_page():
    """Serves the standalone browser microphone voice tester page."""
    html_path = os.path.join(static_dir, "browser_client.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return HTMLResponse("<h1>Browser client not found</h1>", status_code=404)


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
        "title": "Real-Time Voice AI Agent for Real-Estate Sales",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
async def root():
    return {
        "message": "Welcome to EstateStream AI Voice Agent API",
        "docs": "/docs",
        "voice_test_client": "/voice-test",
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
