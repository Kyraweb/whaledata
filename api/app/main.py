import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import species, sightings, routes
from app.admin.admin import router as admin_router

app = FastAPI(
    title="whaledata.org API",
    description="Open whale population, sighting, and migration data from around the world.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://whaledata.org",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(species.router)
app.include_router(sightings.router)
app.include_router(routes.router)
app.include_router(admin_router)

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "whaledata-api"}
