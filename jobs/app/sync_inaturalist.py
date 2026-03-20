"""
sync_inaturalist.py

Fetches research-grade whale observations from iNaturalist API.
Only pulls research-grade records (community-verified).

iNaturalist API: https://api.inaturalist.org/v1/docs

Usage:
    python -m app.sync_inaturalist
    python -m app.sync_inaturalist --debug
    python -m app.sync_inaturalist --limit=500
"""

import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime
from app.database import get_connection

# ── Config ────────────────────────────────────────────────────

DEBUG       = "--debug" in sys.argv
LIMIT_ARG   = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--limit=")), None)
MAX_RECORDS = LIMIT_ARG or 1200
PAGE_SIZE   = 200  # iNaturalist max per page

INAT_API = "https://api.inaturalist.org/v1"

# iNaturalist taxon IDs for whale species
TARGET_SPECIES = [
    {"taxon_id": 41472,  "common_name": "Humpback whale", "scientific_name": "Megaptera novaeangliae"},
    {"taxon_id": 41473,  "common_name": "Blue whale",     "scientific_name": "Balaenoptera musculus"},
    {"taxon_id": 41474,  "common_name": "Fin whale",      "scientific_name": "Balaenoptera physalus"},
    {"taxon_id": 41476,  "common_name": "Grey whale",     "scientific_name": "Eschrichtius robustus"},
    {"taxon_id": 41490,  "common_name": "Sperm whale",    "scientific_name": "Physeter macrocephalus"},
    {"taxon_id": 41498,  "common_name": "Orca",           "scientific_name": "Orcinus orca"},
]


def log(msg, force=False):
    if DEBUG or force:
        print(msg, flush=True)


def fetch_inat_page(taxon_id: int, page: int) -> dict:
    """Fetch one page of research-grade iNaturalist observations."""
    params = {
        "taxon_id":     taxon_id,
        "quality_grade": "research",
        "per_page":     PAGE_SIZE,
        "page":         page,
        "geo":          "true",      # must have coordinates
        "order":        "desc",
        "order_by":     "created_at",
        "fields":       "id,taxon,observed_on,location,place_guess,uri,photos,user",
    }
    url = f"{INAT_API}/observations?" + urllib.parse.urlencode(params)
    log(f"  Fetching: {url}")
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "whaledata.org/1.0 (contact: hello@whaledata.org)",
                "Accept": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        log(f"  [HTTP ERROR] {e.code} {e.reason}", force=True)
        return {}
    except Exception as e:
        log(f"  [ERROR] {e}", force=True)
        return {}


def parse_location(location_str: str):
    """Parse iNaturalist 'lat,lng' location string."""
    if not location_str:
        return None, None
    try:
        parts = location_str.split(",")
        return float(parts[0]), float(parts[1])
    except Exception:
        return None, None


def insert_inat(conn, record: dict, common_name: str, scientific_name: str) -> str:
    cur = conn.cursor()
    try:
        source_id = str(record.get("id", ""))
        location  = record.get("location", "")
        lat, lng  = parse_location(location)

        if not source_id or lat is None or lng is None:
            log(f"  [SKIP] No coords: id={source_id}")
            return "skipped"

        observed_on   = record.get("observed_on") or None
        quality_grade = record.get("quality_grade", "research")
        region        = record.get("place_guess") or ""
        source_url    = record.get("uri") or f"https://www.inaturalist.org/observations/{source_id}"
        observer      = record.get("user", {}).get("login", "") if record.get("user") else ""

        # Get first photo URL if available
        photos    = record.get("photos", [])
        image_url = photos[0].get("url", "").replace("square", "medium") if photos else None

        cur.execute("""
            INSERT INTO inaturalist_sightings (
                common_name, scientific_name, location, observed_on,
                quality_grade, region, source_id, source_url, image_url, observer
            ) VALUES (
                %s, %s,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (source_id) DO NOTHING;
        """, (
            common_name, scientific_name,
            lng, lat,
            observed_on, quality_grade, region,
            source_id, source_url, image_url, observer
        ))
        conn.commit()
        result = "inserted" if cur.rowcount > 0 else "skipped"
        log(f"  [{result.upper()}] {common_name} @ {lat:.2f},{lng:.2f} on {observed_on} by {observer}")
        return result

    except Exception as e:
        conn.rollback()
        log(f"  [ERROR] Insert failed: {e}", force=True)
        return "error"
    finally:
        cur.close()


def sync_species(conn, species: dict) -> dict:
    counts = {"fetched": 0, "inserted": 0, "skipped": 0, "error": 0}
    log(f"\n→ Syncing {species['common_name']} from iNaturalist...", force=True)

    page = 1
    while counts["fetched"] < MAX_RECORDS:
        data    = fetch_inat_page(species["taxon_id"], page)
        records = data.get("results", [])
        total   = data.get("total_results", 0)

        if not records:
            log(f"  No more records (total available: {total})")
            break

        counts["fetched"] += len(records)
        log(f"  Page {page}: {len(records)} records (total available: {total})")

        for r in records:
            result = insert_inat(conn, r, species["common_name"], species["scientific_name"])
            counts[result] = counts.get(result, 0) + 1

        log(f"  Running — inserted: {counts['inserted']}, skipped: {counts['skipped']}")

        if len(records) < PAGE_SIZE or counts["fetched"] >= total:
            break
        page += 1

    log(f"  Done — inserted: {counts['inserted']}", force=True)
    return counts


def log_sync(conn, total: dict, error_msg: str = None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sync_log (source, started_at, completed_at, records_fetched,
                              records_inserted, records_skipped, status, error_message)
        VALUES ('inaturalist', NOW(), NOW(), %s, %s, %s, %s, %s);
    """, (total["fetched"], total["inserted"], total["skipped"],
          "failed" if error_msg else "success", error_msg))
    conn.commit()
    cur.close()


def run():
    print("=" * 52)
    print("whaledata — iNaturalist sync")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if DEBUG: print("DEBUG MODE ON")
    print("=" * 52)

    total = {"fetched": 0, "inserted": 0, "skipped": 0, "error": 0}
    error_msg = None

    try:
        conn = get_connection()
        for species in TARGET_SPECIES:
            counts = sync_species(conn, species)
            for k in total:
                total[k] += counts.get(k, 0)
        log_sync(conn, total)
        conn.close()
    except Exception as e:
        error_msg = str(e)
        print(f"\n[FATAL ERROR] {e}", flush=True)
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 52)
    print("Sync complete")
    print(f"  Fetched:  {total['fetched']}")
    print(f"  Inserted: {total['inserted']}")
    print(f"  Skipped:  {total['skipped']}")
    if error_msg:
        print(f"  Fatal:    {error_msg}")
    print("=" * 52)


if __name__ == "__main__":
    run()
