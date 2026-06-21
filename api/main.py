"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.routes import videos, violations
from api.schemas import HealthResponse
from database.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Helmet Violation Detection API",
    description="Sri Lankan helmet violation detection from traffic video",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos.router)
app.include_router(violations.router)


@app.get("/api/health", response_model=HealthResponse)
def health():
    dialect = "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql"
    return HealthResponse(
        status="ok",
        storage_backend=settings.STORAGE_BACKEND,
        use_celery=settings.USE_CELERY,
        use_mock_models=settings.USE_MOCK_MODELS,
        database_dialect=dialect,
    )
