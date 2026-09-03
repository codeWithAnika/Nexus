from fastapi import FastAPI

from app.api.routes.cases import router as cases_router

app = FastAPI(
    title="Nexus - AI Criminal Network Analysis System",
    description="Backend API for criminal network analysis and investigation.",
    version="1.0.0",
)

app.include_router(cases_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Nexus Backend is running",
        "status": "success",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}