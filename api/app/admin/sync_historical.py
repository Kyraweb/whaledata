"""
sync_historical.py

Fetches historical whale sighting records from GBIF.
These are pre-1950 records from digitised whaling logs,
museum specimens, and historical surveys.

Targets the same species but filters for old records only.

Usage:
    python -m app.sync_historical
    python -m app.sync_historical --debug
    python -m app.sync_historical --limit=500
"""

import sys
import requests
from datetime import datetime
from app.admin.sync_db import get_connection

# ── Config ────────────────────────────────────────────────────

DEBUG       = "--debug" in sys.argv
LIMIT_ARG   = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--limit=")), None)
MAX_RECORDS = LIMIT_ARG or 1200
BATCH_SIZE  = 300
CUTOFF_YEAR = 1950  # only fetch records before this year

GBIF_API = "https://api.gbif.org/v1/occurrence/search"

TARGET_SPECIES = [
    {"taxon_key": 2440898, "common_name": "Humpback whale", "scientific_name": "Megaptera novaeangliae"},
    {"taxon_key": 2440718, "common_name": "Blue whale",     "scientific_name": "Balaenoptera musculus"},
    {"taxon_key": 2440483, "common_name": "Orca",           "scientific_name": "Orcinus orca"},
    {"taxon_key": 2440714, "common_name": "Grey whale",     "scientific_name": "Eschrichtius robustus"},
    {"taxon_key": 2440764, "common_name": "Sperm whale",    "scientific_name": "Physeter macrocephalus"},
    {"taxon_key": 2440706, "common_name": "Fin whale",      "scientific_name": "Balaenoptera physalus"},
]


def log(msg, force=False):
    if DEBUG or force:
        print(msg, flush=True)


def fetch_gbif_historical(taxon_key: int, offset: int) -> list:
    """Fetch pre-1950 GBIF records for a species."""
    params = {
        "taxonKey":         taxon_key,
        "hasCoordinate":    "true",
        "hasGeospatialIssue": "false",
        "year":             f"1500,{CUTOFF_YEAR}",  # GBIF range format: minYear,maxYear
        "limit":            BATCH_SIZE,
        "offset":           offset,
    }
    log(f"  Fetching GBIF historical offset={offset}...")
    try:
        r = requests.get(GBIF_API, params=params, timeout=30,
                        headers={"User-Agent": "whaledata.org/1.0"})
        r.raise_for_status()
        return r.json().get("results", [])
    except requests.HTTPError as e:
        log(f"  [HTTP ERROR] {e}", force=True)
        return []
    except Exception as e:
        log(f"  [ERROR] {e}", force=True)
        return []


def parse_year(record: dict):
    """Extract year from GBIF record."""
    return record.get("year") or record.get("eventDate", "")[:4] or None


def parse_date(raw):
    """Handle partial dates: year-only, year-month, full date, ranges."""
    if not raw:
        return None
    raw = str(raw).strip()
    if "/" in raw:
        raw = raw.split("/")[0].strip()
    if len(raw) < 4 or not raw[:4].isdigit() or not (1000 <= int(raw[:4]) <= 2099):
        return None
    if len(raw) == 10 and raw.count("-") == 2:
        return raw
    if len(raw) == 7 and raw.count("-") == 1:
        return raw + "-01"
    if len(raw) == 4:
        return raw + "-01-01"
    return raw[:10]

def insert_historical(conn, record: dict, common_name: str, scientific_name: str) -> str:
    cur = conn.cursor()
    try:
        source_id = str(record.get("key", ""))
        lat = record.get("decimalLatitude")
        lng = record.get("decimalLongitude")

        if not source_id or lat is None or lng is None:
            return "skipped"

        year       = parse_year(record)
        sighted_on = parse_date(record.get("eventDate"))
        region     = record.get("country") or record.get("stateProvince") or ""

        # Try to extract vessel name from occurrenceRemarks or dataset
        notes = record.get("occurrenceRemarks") or ""
        vessel = None
        if "ship" in notes.lower() or "vessel" in notes.lower() or "whaling" in notes.lower():
            vessel = notes[:200]

        source_url = f"https://www.gbif.org/occurrence/{source_id}"

        cur.execute("""
            INSERT INTO historical_sightings (
                common_name, scientific_name, location, sighted_on,
                year, vessel, region, source, source_id, source_url
            ) VALUES (
                %s, %s,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s, %s, %s, %s,
                'gbif_historical', %s, %s
            )
            ON CONFLICT (source, source_id) DO NOTHING;
        """, (
            common_name, scientific_name,
            lng, lat,
            sighted_on, year, vessel, region,
            source_id, source_url
        ))
        conn.commit()
        result = "inserted" if cur.rowcount > 0 else "skipped"
        log(f"  [{result.upper()}] {common_name} @ {lat:.2f},{lng:.2f} year={year}")
        return result

    except Exception as e:
        conn.rollback()
        log(f"  [ERROR] Insert failed: {e}", force=True)
        return "error"
    finally:
        cur.close()


def sync_species(conn, species: dict) -> dict:
    counts = {"fetched": 0, "inserted": 0, "skipped": 0, "error": 0}
    log(f"\n→ Syncing {species['common_name']} historical records...", force=True)

    offset = 0
    while counts["fetched"] < MAX_RECORDS:
        records = fetch_gbif_historical(species["taxon_key"], offset)
        if not records:
            log("  No more records.")
            break

        counts["fetched"] += len(records)
        log(f"  Batch offset {offset}: {len(records)} records")

        for r in records:
            result = insert_historical(conn, r, species["common_name"], species["scientific_name"])
            counts[result] = counts.get(result, 0) + 1

        log(f"  Running — inserted: {counts['inserted']}, skipped: {counts['skipped']}")
        offset += len(records)

        if len(records) < BATCH_SIZE:
            break

    log(f"  Done — inserted: {counts['inserted']}", force=True)
    return counts


def log_sync(conn, total: dict, error_msg: str = None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sync_log (source, started_at, completed_at, records_fetched,
                              records_inserted, records_skipped, status, error_message)
        VALUES ('historical', NOW(), NOW(), %s, %s, %s, %s, %s);
    """, (total["fetched"], total["inserted"], total["skipped"],
          "failed" if error_msg else "success", error_msg))
    conn.commit()
    cur.close()


def run():
    print("=" * 52)
    print(f"whaledata — Historical sync (GBIF pre-{CUTOFF_YEAR})")
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
