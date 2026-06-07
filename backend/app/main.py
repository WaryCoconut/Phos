from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import game, diplomacy, advisor, scenarios, regions, maps

app = FastAPI(
    title="OpenPaxHistoria",
    description="Simulation géopolitique narrative alimentée par IA",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game.router, prefix="/api")
app.include_router(diplomacy.router, prefix="/api")
app.include_router(advisor.router, prefix="/api")
app.include_router(scenarios.router, prefix="/api")
app.include_router(regions.router, prefix="/api")
app.include_router(maps.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "api_base_url": settings.api_base_url,
        "model": settings.model,
    }
