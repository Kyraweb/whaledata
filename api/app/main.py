import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import species, sightings, routes, strandings, acoustics, inaturalist, historical, layers, alerts
from app.admin.admin import router as admin_router

app = FastAPI(
    title="whaledata.org API",
    description="Open whale population, sighting, and migration data from around the world.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://whaledata.org",
        "http://localhost:5173",
        "https://docs.whaledata.org",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core routers
app.include_router(species.router)
app.include_router(sightings.router)
app.include_router(routes.router)

# Phase 2 — Data layers
app.include_router(strandings.router)
app.include_router(acoustics.router)
app.include_router(inaturalist.router)
app.include_router(historical.router)
app.include_router(layers.router)
app.include_router(alerts.router)

# Admin panel
app.include_router(admin_router)

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "whaledata-api", "version": "2.0.0"}
