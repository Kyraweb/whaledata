import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import species, sightings, routes, strandings, acoustics, inaturalist, historical, layers, alerts
from app.admin.admin import router as admin_router
from app.middleware import log_request_bg, should_log
import time

app = FastAPI(
    title="whaledata.org API",
    description="Open whale population, sighting, and migration data from around the world.",
    version="2.0.0"
)

@app.middleware("http")
async def usage_logging(request, call_next):
    from starlette.requests import Request
    import threading
    path = request.url.path
    start = time.time()
    response = await call_next(request)
    if should_log(path):
        duration = round((time.time() - start) * 1000)
        ip = (request.headers.get("x-forwarded-for") or
              (request.client.host if request.client else "unknown")).split(",")[0].strip()
        threading.Thread(
            target=log_request_bg,
            args=(ip, path, request.method, response.status_code, duration),
            daemon=True
        ).start()
    return response

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
