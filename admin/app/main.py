import os
import secrets
import subprocess
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from app.database import get_connection

load_dotenv()

app = FastAPI(title="whaledata admin", docs_url=None, redoc_url=None)
security = HTTPBasic()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

ADMIN_USER     = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")


# ── Auth ──────────────────────────────────────────────────────

def require_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username.encode(), ADMIN_USER.encode())
    correct_pass = secrets.compare_digest(credentials.password.encode(), ADMIN_PASSWORD.encode())
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# ── Helpers ───────────────────────────────────────────────────

def get_dashboard_data():
    conn = get_connection()
    cur  = conn.cursor()

    # Total sightings
    cur.execute("SELECT COUNT(*) as total FROM sightings;")
    total_sightings = cur.fetchone()["total"]

    # Per species counts
    cur.execute("""
        SELECT common_name, COUNT(*) as count, source,
               MIN(sighted_on) as earliest, MAX(sighted_on) as latest
        FROM sightings
        GROUP BY common_name, source
        ORDER BY common_name, source;
    """)
    species_counts = cur.fetchall()

    # Last sync per source
    cur.execute("""
        SELECT source, status, started_at, finished_at,
               records_fetched, records_inserted, records_skipped, error_message
        FROM sync_log
        ORDER BY started_at DESC
        LIMIT 10;
    """)
    recent_syncs = cur.fetchall()

    # DB size
    cur.execute("SELECT pg_size_pretty(pg_database_size(current_database())) as size;")
    db_size = cur.fetchone()["size"]

    # Species in species table
    cur.execute("SELECT id, common_name, scientific_name, conservation_status, population_trend FROM species ORDER BY common_name;")
    species_list = cur.fetchall()

    # Migration routes count
    cur.execute("SELECT COUNT(*) as total FROM migration_routes;")
    routes_count = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return {
        "total_sightings": total_sightings,
        "species_counts":  species_counts,
        "recent_syncs":    recent_syncs,
        "db_size":         db_size,
        "species_list":    species_list,
        "routes_count":    routes_count,
    }


def get_sync_logs(limit: int = 50):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT source, status, started_at, finished_at,
               records_fetched, records_inserted, records_skipped, error_message,
               EXTRACT(EPOCH FROM (finished_at - started_at))::int as duration_seconds
        FROM sync_log
        ORDER BY started_at DESC
        LIMIT %s;
    """, (limit,))
    logs = cur.fetchall()
    cur.close()
    conn.close()
    return logs


# ── Routes ────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, user: str = Depends(require_auth)):
    data = get_dashboard_data()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user":    user,
        "now":     datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        **data
    })


@app.get("/logs", response_class=HTMLResponse)
def sync_logs(request: Request, user: str = Depends(require_auth)):
    logs = get_sync_logs(100)
    return templates.TemplateResponse("logs.html", {
        "request": request,
        "user":    user,
        "logs":    logs,
        "now":     datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
    })


@app.get("/species", response_class=HTMLResponse)
def species_page(request: Request, user: str = Depends(require_auth)):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT s.id, s.common_name, s.scientific_name, s.conservation_status,
               s.population_trend, COUNT(si.id) as sighting_count,
               MIN(si.sighted_on) as earliest, MAX(si.sighted_on) as latest
        FROM species s
        LEFT JOIN sightings si ON si.common_name = s.common_name
        GROUP BY s.id, s.common_name, s.scientific_name, s.conservation_status, s.population_trend
        ORDER BY s.common_name;
    """)
    species = cur.fetchall()
    cur.close()
    conn.close()
    return templates.TemplateResponse("species.html", {
        "request": request,
        "user":    user,
        "species": species,
        "now":     datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
    })


@app.get("/sync", response_class=HTMLResponse)
def sync_page(request: Request, user: str = Depends(require_auth)):
    logs = get_sync_logs(5)
    return templates.TemplateResponse("sync.html", {
        "request": request,
        "user":    user,
        "logs":    logs,
        "now":     datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
    })


@app.post("/sync/trigger/{job}")
def trigger_sync(job: str, user: str = Depends(require_auth)):
    """Trigger a sync job and return status."""
    allowed = {"gbif": "app.sync_gbif", "obis": "app.sync_obis"}
    if job not in allowed:
        raise HTTPException(status_code=400, detail="Unknown job")

    try:
        result = subprocess.run(
            ["python", "-m", allowed[job]],
            capture_output=True, text=True, timeout=3600
        )
        return JSONResponse({
            "status":  "success" if result.returncode == 0 else "error",
            "stdout":  result.stdout[-3000:],  # last 3000 chars
            "stderr":  result.stderr[-1000:],
            "code":    result.returncode
        })
    except subprocess.TimeoutExpired:
        return JSONResponse({"status": "timeout", "stdout": "", "stderr": "Timed out after 1 hour", "code": -1})
    except Exception as e:
        return JSONResponse({"status": "error", "stdout": "", "stderr": str(e), "code": -1})


@app.get("/health")
def health():
    return {"status": "ok", "service": "whaledata-admin"}
