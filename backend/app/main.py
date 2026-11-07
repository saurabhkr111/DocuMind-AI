from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from backend.app.database.connection import init_db
from backend.app import models
from backend.app.routes.workflow import router as workflow_router
from backend.app.routes.github import router as github_router
from backend.app.routes.agents import router as agents_router
from backend.app.routes.documents import router as documents_router
from backend.app.routes.switch import router as switch_router


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
app.include_router(agents_router)
app.include_router(documents_router)
app.include_router(switch_router)


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
        "orchestrator": "Python AgentOrchestrator",
        "switch_integration": "webhook_available",
        "backend": "FastAPI"
    }


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema.setdefault("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API Key",
            "description": (
                "Provide a DocuMind API key as a Bearer token. "
                "Configure keys via DOCU_MIND_API_KEYS."
            ),
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

