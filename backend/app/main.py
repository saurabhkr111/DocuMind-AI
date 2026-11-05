from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI

from backend.app.database.connection import init_db
from backend.app import models
from backend.app.routes.workflow import router as workflow_router
from backend.app.routes.github import router as github_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application startup
    init_db()

    yield

    # Application shutdown
    pass


app = FastAPI(
    title="DocuMind AI",
    description="AI-powered Documentation and Team Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(workflow_router)
app.include_router(github_router)


@app.get("/")
def home():
    return {
        "project": "DocuMind AI",
        "message": "Welcome to DocuMind AI!",
        "description": "AI-powered documentation and team intelligence platform",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "DocuMind AI Backend",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/v1/info")
def project_info():
    return {
        "project_name": "DocuMind AI",
        "version": "1.0.0",
        "agents": [
            "Documentation Agent",
            "Code Review Agent",
            "Team Intelligence Agent"
        ],
        "orchestrator": "Switch",
        "backend": "FastAPI"
    }