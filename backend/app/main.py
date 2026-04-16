from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.core.database import init_db
from app.core.paths import ensure_runtime_dirs
from app.services.cleanup_service import cleanup_empty_dirs
from app.services.dependency_checks import check_dependencies

@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_runtime_dirs()
    init_db()
    cleanup_empty_dirs(settings.data_dir / "segments")
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
def health() -> dict:
    return {"ok": True, "dependencies": check_dependencies()}


app.include_router(router)
