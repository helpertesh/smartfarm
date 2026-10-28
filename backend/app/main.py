from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.db.session import Base, engine
from app.routers import admin, advisory, alerts, analytics, auth, calendar, diseases, farms, inputs, irrigation, market, weather
from app.seed import seed_market_prices

settings = get_settings()
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    import app.models  # noqa: F401  ensure models are registered

    Base.metadata.create_all(bind=engine)
    seed_market_prices()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Weather intelligence, crop advisory, crop calendar, disease information, irrigation advice, market prices and farm analytics for smallholder farmers.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, farms, weather, advisory, calendar, diseases, irrigation, market, analytics, inputs, alerts, admin):
    app.include_router(r.router)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok", "app": settings.app_name}


# Serve the frontend from the same server in development (API routes above take priority).
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
