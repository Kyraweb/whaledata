import os
import secrets
from datetime import datetime

from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

from app.database import get_connection

router   = APIRouter(prefix="/admin")
security = HTTPBasic()

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

ADMIN_USER     = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")


def require_auth(credentials: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(credentials.username.encode(), ADMIN_USER.encode())
    ok_pass = secrets.compare_digest(credentials.password.encode(), ADMIN_PASSWORD.encode())
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M UTC")


# ── Dashboard ─────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, user: str = Depends(require_auth)):
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) as n FROM sightings;")
    total_sightings = cur.fetchone()["n"]

    cur.execute("""
        SELECT common_name, source, COUNT(*) as n,
               MIN(sighted_on) as earliest, MAX(sighted_on) as latest
        FROM sightings
        GROUP BY common_name, source
        ORDER BY common_name, source;
    """)
    species_counts = cur.fetchall()

    cur.execute("SELECT pg_size_pretty(pg_database_size(current_database())) as size;")
    db_size = cur.fetchone()["size"]

    cur.execute("SELECT COUNT(*) as n FROM species;")
    species_total = cur.fetchone()["n"]

    cur.execute("SELECT COUNT(*) as n FROM migration_routes;")
    routes_total = cur.fetchone()["n"]

    try:
        cur.execute("""
            SELECT source, status, started_at,
                   records_fetched, records_inserted, records_skipped, error_message
            FROM sync_log ORDER BY started_at DESC LIMIT 10;
        """)
        sync_logs = cur.fetchall()
    except Exception:
        sync_logs = []

    cur.close()
    conn.close()

    return templates.TemplateResponse("dashboard.html", {
        "request":        request,
        "now":            now(),
        "total_sightings": total_sightings,
        "species_counts": species_counts,
        "db_size":        db_size,
        "species_total":  species_total,
        "routes_total":   routes_total,
        "sync_logs":      sync_logs,
    })


# ── Species ───────────────────────────────────────────────────

@router.get("/species", response_class=HTMLResponse)
def species_page(request: Request, user: str = Depends(require_auth), msg: str = ""):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT s.id, s.common_name, s.scientific_name,
               s.conservation_status, s.population_trend,
               COUNT(si.id) as sighting_count
        FROM species s
        LEFT JOIN sightings si ON si.common_name = s.common_name
        GROUP BY s.id ORDER BY s.common_name;
    """)
    species = cur.fetchall()
    cur.close()
    conn.close()
    return templates.TemplateResponse("species.html", {
        "request": request, "now": now(),
        "species": species, "msg": msg,
    })


@router.post("/species/edit")
async def edit_species(
    request: Request,
    species_id: int = Form(...),
    conservation_status: str = Form(...),
    population_trend: str = Form(...),
    user: str = Depends(require_auth)
):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        UPDATE species SET conservation_status=%s, population_trend=%s, updated_at=NOW()
        WHERE id=%s;
    """, (conservation_status, population_trend, species_id))
    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse("/admin/species?msg=Updated+successfully", status_code=303)


# ── Sightings ─────────────────────────────────────────────────

@router.get("/sightings", response_class=HTMLResponse)
def sightings_page(
    request: Request,
    user: str = Depends(require_auth),
    species: str = "",
    source: str = "",
    region: str = "",
    msg: str = "",
):
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) as n FROM sightings;")
    total = cur.fetchone()["n"]

    cur.execute("SELECT DISTINCT common_name FROM sightings ORDER BY common_name;")
    species_list = [r["common_name"] for r in cur.fetchall()]

    conditions, params = [], []
    if species: conditions.append("common_name = %s"); params.append(species)
    if source:  conditions.append("source = %s");      params.append(source)
    if region:  conditions.append("region ILIKE %s");  params.append(f"%{region}%")
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(200)

    cur.execute(f"""
        SELECT id, common_name, source, sighted_on, region,
               ST_Y(location::geometry) as lat,
               ST_X(location::geometry) as lng
        FROM sightings {where}
        ORDER BY id DESC LIMIT %s;
    """, params)
    sightings = cur.fetchall()
    cur.close()
    conn.close()

    return templates.TemplateResponse("sightings.html", {
        "request": request, "now": now(),
        "sightings": sightings, "total": total,
        "species_list": species_list,
        "sel_species": species, "sel_source": source, "sel_region": region,
        "msg": msg,
    })


@router.post("/sightings/delete")
def delete_sighting(
    sighting_id: int = Form(...),
    back: str = Form(""),
    user: str = Depends(require_auth),
):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("DELETE FROM sightings WHERE id=%s;", (sighting_id,))
    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse(f"/admin/sightings?msg=Deleted&{back}", status_code=303)


# ── Sync logs ─────────────────────────────────────────────────

@router.get("/logs", response_class=HTMLResponse)
def logs_page(request: Request, user: str = Depends(require_auth)):
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT source, status, started_at, completed_at,
                   records_fetched, records_inserted, records_skipped, error_message,
                   CASE WHEN completed_at IS NOT NULL AND started_at IS NOT NULL
                        THEN EXTRACT(EPOCH FROM (completed_at - started_at))::int
                        ELSE NULL END as duration_sec
            FROM sync_log ORDER BY started_at DESC LIMIT 100;
        """)
        logs = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        logs = []
        import traceback
        error = traceback.format_exc()
        return templates.TemplateResponse("logs.html", {
            "request": request, "now": now(), "logs": logs, "error": error,
        })
    return templates.TemplateResponse("logs.html", {
        "request": request, "now": now(), "logs": logs, "error": None,
    })


# ── Manual Sync ───────────────────────────────────────────────

@router.get("/sync", response_class=HTMLResponse)
def sync_page(request: Request, user: str = Depends(require_auth)):
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT source, status, started_at, records_inserted, records_skipped
            FROM sync_log ORDER BY started_at DESC LIMIT 10;
        """)
        logs = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        logs = []
    return templates.TemplateResponse("sync.html", {
        "request": request, "now": now(), "logs": logs,
    })


@router.post("/sync/run/{job}")
def run_sync(job: str, user: str = Depends(require_auth)):
    import subprocess
    allowed = {
        "gbif":        "app.admin.sync_gbif",
        "obis":        "app.admin.sync_obis",
        "strandings":  "app.admin.sync_strandings",
        "acoustics":   "app.admin.sync_acoustics",
        "inaturalist": "app.admin.sync_inaturalist",
        "historical":  "app.admin.sync_historical",
    }
    if job not in allowed:
        from fastapi.responses import JSONResponse
        return JSONResponse({"status": "error", "output": "Unknown job"})

    try:
        result = subprocess.run(
            ["python", "-m", allowed[job]],
            capture_output=True, text=True, timeout=3600,
            cwd="/app"
        )
        output = result.stdout + ("\n--- STDERR ---\n" + result.stderr if result.stderr.strip() else "")
        return {"status": "success" if result.returncode == 0 else "error", "output": output[-4000:]}
    except subprocess.TimeoutExpired:
        return {"status": "error", "output": "Timed out after 1 hour"}
    except Exception as e:
        return {"status": "error", "output": str(e)}


# ── Alert Subscribers ─────────────────────────────────────────

@router.get("/subscribers", response_class=HTMLResponse)
def subscribers_page(request: Request, user: str = Depends(require_auth)):
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, email, confirmed, species_filter, region_filter, layer_filter,
                   created_at, last_sent_at
            FROM alert_subscribers
            ORDER BY created_at DESC;
        """)
        subscribers = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        subscribers = []
    return templates.TemplateResponse("subscribers.html", {
        "request": request, "now": now(),
        "subscribers": subscribers,
        "total": len(subscribers),
        "confirmed": sum(1 for s in subscribers if s["confirmed"]),
    })


@router.get("/subscribers/export")
def export_subscribers(user: str = Depends(require_auth)):
    from fastapi.responses import StreamingResponse
    import csv, io

    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT email, confirmed, species_filter, region_filter, layer_filter,
               created_at, last_sent_at
        FROM alert_subscribers
        WHERE confirmed = TRUE
        ORDER BY created_at DESC;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["email", "confirmed", "species", "region", "layer", "subscribed_at", "last_sent_at"])
    for r in rows:
        writer.writerow([
            r["email"], r["confirmed"],
            r["species_filter"] or "all",
            r["region_filter"]  or "all",
            r["layer_filter"]   or "all",
            r["created_at"].strftime("%Y-%m-%d") if r["created_at"] else "",
            r["last_sent_at"].strftime("%Y-%m-%d") if r["last_sent_at"] else "never",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=whaledata_subscribers.csv"}
    )


@router.post("/subscribers/delete")
def delete_subscriber(
    subscriber_id: int = Form(...),
    user: str = Depends(require_auth),
):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("DELETE FROM alert_subscribers WHERE id = %s;", (subscriber_id,))
    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse("/admin/subscribers?msg=Deleted", status_code=303)
