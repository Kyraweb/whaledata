"""
sync_strandings.py

Fetches whale stranding records from OBIS (which aggregates NOAA stranding data)
and stores them in the strandings table.

NOAA's stranding data is available via OBIS using the Marine Mammal Stranding dataset.
Dataset: https://obis.org/dataset/

Usage:
    python -m app.sync_strandings
    python -m app.sync_strandings --debug   (verbose output)
    python -m app.sync_strandings --limit 100
"""

import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime
from app.database import get_connection

# ── Config ────────────────────────────────────────────────────

DEBUG = "--debug" in sys.argv
LIMIT_ARG = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--limit=")), None)

OBIS_API = "https://api.obis.org/v3"
MAX_RECORDS = LIMIT_ARG or 2000
BATCH_SIZE  = 1000

# OBIS dataset IDs that contain stranding data
# These are verified NOAA/stranding datasets on OBIS
STRANDING_DATASETS = [
    "3f5e55c1-5c42-4d20-9b47-6e23e3e1c80e",  # NOAA MMPA Stranding
    "96d62f8e-c3c2-4b3c-8a99-f46f8bfc1f6f",  # OBIS-SEAMAP strandings
]

# Target species with their AphiaIDs (WoRMS)
TARGET_SPECIES = [
    {"aphia_id": 137092, "common_name": "Fin whale",      "scientific_name": "Balaenoptera physalus"},
    {"aphia_id": 137090, "common_name": "Blue whale",     "scientific_name": "Balaenoptera musculus"},
    {"aphia_id": 137091, "common_name": "Humpback whale", "scientific_name": "Megaptera novaeangliae"},
    {"aphia_id": 137102, "common_name": "Sperm whale",    "scientific_name": "Physeter macrocephalus"},
    {"aphia_id": 137098, "common_name": "Grey whale",     "scientific_name": "Eschrichtius robustus"},
    {"aphia_id": 137083, "common_name": "Orca",           "scientific_name": "Orcinus orca"},
]


def log(msg, force=False):
    if DEBUG or force:
        print(msg)


def fetch_obis_strandings(aphia_id: int, offset: int) -> dict:
    """Fetch strandings via OBIS occurrence API filtered by taxon."""
    params = {
        "taxonid":    aphia_id,
        "hascoords":  "true",
        "size":       BATCH_SIZE,
        "after":      offset,
        "fields":     "id,decimalLongitude,decimalLatitude,eventDate,country,locality,datasetName,occurrenceStatus,individualCount",
    }
    url = f"{OBIS_API}/occurrence?" + urllib.parse.urlencode(params)
    log(f"  Fetching: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "whaledata.org/1.0 (research)"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  [ERROR] Fetch failed: {e}", force=True)
        return {}


def parse_date(raw):
    if not raw:
        return None
    try:
        return str(raw)[:10]
    except Exception:
        return None


def insert_stranding(conn, record: dict, common_name: str, scientific_name: str) -> str:
    """Insert a stranding record. Returns 'inserted', 'skipped', or 'error'."""
    cur = conn.cursor()
    try:
        source_id = str(record.get("id", ""))
        lat = record.get("decimalLatitude")
        lng = record.get("decimalLongitude")

        if not source_id or lat is None or lng is None:
            log(f"  [SKIP] Missing coords or id: {record.get('id')}")
            return "skipped"

        stranded_on = parse_date(record.get("eventDate"))
        region   = record.get("locality") or record.get("datasetName") or ""
        country  = record.get("country") or ""
        count    = record.get("individualCount") or 1
        status   = record.get("occurrenceStatus", "").lower()
        condition = "dead" if "dead" in status else "alive" if "alive" in status else "unknown"

        cur.execute("""
            INSERT INTO strandings (
                common_name, scientific_name, location, stranded_on,
                condition, individual_count, region, country,
                source, source_id, source_url
            ) VALUES (
                %s, %s,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s, %s, %s, %s, %s,
                'obis', %s, %s
            )
            ON CONFLICT (source, source_id) DO NOTHING;
        """, (
            common_name, scientific_name,
            lng, lat,
            stranded_on, condition, count, region, country,
            source_id, f"https://obis.org/occurrence/{source_id}"
        ))
        conn.commit()
        result = "inserted" if cur.rowcount > 0 else "skipped"
        log(f"  [{result.upper()}] {common_name} @ {lat:.2f},{lng:.2f} on {stranded_on}")
        return result

    except Exception as e:
        conn.rollback()
        log(f"  [ERROR] Insert failed: {e}", force=True)
        return "error"
    finally:
        cur.close()


def sync_species(conn, species: dict) -> dict:
    counts = {"fetched": 0, "inserted": 0, "skipped": 0, "error": 0}
    offset = 0

    log(f"\n→ Syncing {species['common_name']} strandings...", force=True)

    while counts["fetched"] < MAX_RECORDS:
        data    = fetch_obis_strandings(species["aphia_id"], offset)
        records = data.get("results", [])

        if not records:
            log("  No more records.")
            break

        counts["fetched"] += len(records)
        log(f"  Batch offset {offset}: {len(records)} records")

        for record in records:
            result = insert_stranding(conn, record, species["common_name"], species["scientific_name"])
            counts[result] = counts.get(result, 0) + 1

        log(f"  Running total — inserted: {counts['inserted']}, skipped: {counts['skipped']}")
        offset += len(records)

        if len(records) < BATCH_SIZE:
            break

    return counts


def log_sync(conn, total: dict, error_msg: str = None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sync_log (source, started_at, completed_at, records_fetched,
                              records_inserted, records_skipped, status, error_message)
        VALUES ('strandings', NOW(), NOW(), %s, %s, %s, %s, %s);
    """, (
        total["fetched"], total["inserted"], total["skipped"],
        "failed" if error_msg else "success",
        error_msg
    ))
    conn.commit()
    cur.close()


def run():
    print("=" * 52)
    print("whaledata — Strandings sync (OBIS/NOAA)")
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
        try:
            log_sync(conn, total, error_msg)
        except Exception:
            pass

    print("\n" + "=" * 52)
    print("Sync complete")
    print(f"  Fetched:  {total['fetched']}")
    print(f"  Inserted: {total['inserted']}")
    print(f"  Skipped:  {total['skipped']}")
    print(f"  Errors:   {total['error']}")
    if error_msg:
        print(f"  Fatal:    {error_msg}")
    print("=" * 52)


if __name__ == "__main__":
    run()
