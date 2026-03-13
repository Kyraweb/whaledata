from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import species, sightings, routes

# ----------------------------
# App setup
# ----------------------------
app = FastAPI(
    title="whaledata.org API",
    description="Open whale population, sighting, and migration data from around the world.",
    version="0.1.0"
)

# ----------------------------
# CORS
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://whaledata.org",
        "http://localhost:5173",  # Vue dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Routers
# ----------------------------
app.include_router(species.router)
app.include_router(sightings.router)
app.include_router(routes.router)

# ----------------------------
# Health check
# ----------------------------
@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "whaledata-api"}
