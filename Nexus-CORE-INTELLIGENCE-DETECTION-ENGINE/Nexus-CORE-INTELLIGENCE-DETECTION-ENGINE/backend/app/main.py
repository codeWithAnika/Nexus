from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import models  # Registers SQLAlchemy models
from app.api.routes.alerts import router as alerts_router
from app.api.routes.auth import router as auth_router
from app.api.routes.cases import router as cases_router
from app.api.routes.entities import router as entities_router
from app.api.routes.evidence import router as evidence_router
from app.api.routes.firs import router as firs_router
from app.api.routes.intelligence import router as intelligence_router
from app.api.routes.processing import router as processing_router
from app.api.routes.relationships import router as relationships_router
from app.api.routes.reports import router as reports_router
from app.database.base import Base
from app.database.connection import database_ready, engine


app = FastAPI(
    title="Nexus - AI Criminal Network Analysis System",
    description=(
        "Backend API for criminal network analysis "
        "and investigation."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Creates SQLite tables when the backend starts.
Base.metadata.create_all(bind=engine)


# Authentication routes
app.include_router(auth_router)

# Application routes
app.include_router(cases_router)
app.include_router(evidence_router)
app.include_router(entities_router)
app.include_router(firs_router)
app.include_router(intelligence_router)
app.include_router(relationships_router)
app.include_router(alerts_router)
app.include_router(reports_router)
app.include_router(processing_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Nexus Backend is running",
        "status": "success",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
    }


@app.get("/ready", response_model=None)
def readiness_check() -> dict[str, str] | JSONResponse:
    if not database_ready():
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
            },
        )

    return {
        "status": "ready",
    }