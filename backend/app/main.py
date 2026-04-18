from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_router
from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.logging import configure_logging
from app.core.object_store import ensure_bucket
import app.models  # noqa: F401


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    Base.metadata.create_all(bind=engine)
    if not settings.enable_local_sync_jobs:
        try:
            ensure_bucket()
        except Exception:
            pass
    yield


app = FastAPI(
    title="Kirana Underwriting API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
