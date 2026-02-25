from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.core.config import settings
from app.core.database import Base, engine
from app.api.router import api_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.core.stripe_client import init_stripe

import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: créer dossiers, tables DB, init Stripe."""
    Path("media/products").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    init_stripe()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ── Middleware ──────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)

# ── Static files (images produits) ─────────────────────────────────────────────
app.mount("/media", StaticFiles(directory="media"), name="media")

# ── Routes ──────────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


# ── Health check ────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "version": settings.VERSION}