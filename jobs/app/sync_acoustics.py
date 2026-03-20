"""
sync_acoustics.py — fetches acoustic detections from OBIS acoustic datasets.
NOAA PACM API is not accessible from all hosting environments so we use OBIS.

Usage:
    python -m app.sync_acoustics
    python -m app.sync_acoustics --debug
    python -m app.sync_acoustics --limit=500
"""

import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime
from app.database import get_connection

DEBUG       = "--debug" in sys.argv
LIMIT_ARG   = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--limit=")), None)
MAX_RECORDS = LIMIT_ARG or 1000
BATCH_SIZE  = 500
OBIS_API    = "https://api.obis.org/v3"

TARGET_SPECIES = [
    {"aphia_id": 137091, "common_name": "Humpback whale", "scientific_name": "Megaptera novaeangliae"},
    {"aphia_id": 137090, "common_name": "Blue whale",     "scientific_name": "Balaenoptera musculus"},
    {"aphia_id": 137092, "common_name": "Fin whale",      "scientific_name": "Balaenoptera physalus"},
    {"aphia_id": 137102, "common_name": "Sperm whale",    "scientific_name": "Physeter macrocephalus"},
    {"aphia_id": 137083, "common_name": "Orca",           "scientific_name": "Orcinus orca"},
]

ACOUSTIC_DATASETS = [
    "ce2de8dc-93ca-4003-bad3-46c20f640f8c",
    "0b3f3f32-7a5b-43c0-9a46-3b9994ca9e87",
]

ACOUSTIC_KEYWORDS = ["acoustic","sound","hydrophone","pacm","pam","passive","detection","buoy","mooring"]


def log(msg, force=False):
    if DEBUG or force:
        print(msg, flush=True)


def fetch_obis(aphia_id, offset, dataset_id=None):
    params = {"taxonid": aphia_id, "hascoords": "true", "size": BATCH_SIZE, "after": offset,
               "fields": "id,decimalLongitude,decimalLatitude,eventDate,locality,datasetName,institutionCode"}
    if dataset_id:
        params["datasetid"] = dataset_id
    url = f"{OBIS_API}/occurrence?" + urllib.parse.urlencode(params)
    log(f"  GET {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "whaledata.org/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read()).get("results", [])
    except Exception as e:
        log(f"  [ERROR] {e}", force=True)
        return []


def is_acoustic(record):
    text = " ".join(filter(None, [record.get("datasetName"), record.get("institutionCode"), record.get("locality")])).lower()
    return any(kw in text for kw in ACOUSTIC_KEYWORDS)


def insert(conn, record, common_name, scientific_name):
    cur = conn.cursor()
    try:
        source_id = str(record.get("id", ""))
        lat = record.get("decimalLatitude")
        lng = record.get("decimalLongitude")
        if not source_id or lat is None or lng is None:
            return "skipped"
        detected_on = str(record.get("eventDate") or "")[:10] or None
        platform    = (record.get("datasetName") or record.get("institutionCode") or "")[:255]
        region      = record.get("locality") or ""
        cur.execute("""
            INSERT INTO acoustics (common_name, scientific_name, location, detected_on,
                call_type, confidence, platform, region, source, source_id, source_url)
            VALUES (%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s, 'unknown', 'unknown', %s, %s, 'obis_acoustic', %s, %s)
            ON CONFLICT (source, source_id) DO NOTHING;
        """, (common_name, scientific_name, float(lng), float(lat), detected_on,
              platform, region, source_id, f"https://obis.org/occurrence/{source_id}"))
        conn.commit()
        result = "inserted" if cur.rowcount > 0 else "skipped"
        log(f"  [{result.upper()}] {common_name} @ {lat:.2f},{lng:.2f}")
        return result
    except Exception as e:
        conn.rollback()
        log(f"  [ERROR] {e}", force=True)
        return "error"
    finally:
        cur.close()


def sync_species(conn, species):
    counts = {"fetched": 0, "inserted": 0, "skipped": 0, "error": 0}
    log(f"\n→ {species['common_name']} acoustics...", force=True)

    for dataset_id in ACOUSTIC_DATASETS:
        offset = 0
        while counts["fetched"] < MAX_RECORDS:
            records = fetch_obis(species["aphia_id"], offset, dataset_id)
            if not records: break
            counts["fetched"] += len(records)
            for r in records:
                res = insert(conn, r, species["common_name"], species["scientific_name"])
                counts[res] = counts.get(res, 0) + 1
            offset += len(records)
            if len(records) < BATCH_SIZE: break

    # Broad fallback filtered by acoustic keywords
    if counts["inserted"] == 0:
        log("  Trying broad keyword filter...", force=True)
        offset = 0
        while counts["fetched"] < MAX_RECORDS:
            records = fetch_obis(species["aphia_id"], offset)
            if not records: break
            acoustic = [r for r in records if is_acoustic(r)]
            counts["fetched"] += len(records)
            for r in acoustic:
                res = insert(conn, r, species["common_name"], species["scientific_name"])
                counts[res] = counts.get(res, 0) + 1
            offset += len(records)
            if len(records) < BATCH_SIZE: break

    log(f"  inserted={counts['inserted']} skipped={counts['skipped']}", force=True)
    return counts


def log_sync(conn, total, error_msg=None):
    cur = conn.cursor()
    cur.execute("""INSERT INTO sync_log (source, started_at, completed_at, records_fetched,
        records_inserted, records_skipped, status, error_message)
        VALUES ('acoustics', NOW(), NOW(), %s, %s, %s, %s, %s);""",
        (total["fetched"], total["inserted"], total["skipped"],
         "failed" if error_msg else "success", error_msg))
    conn.commit()
    cur.close()


def run():
    print("=" * 52)
    print("whaledata — Acoustics sync (OBIS)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if DEBUG: print("DEBUG MODE ON")
    print("=" * 52)
    total = {"fetched": 0, "inserted": 0, "skipped": 0, "error": 0}
    error_msg = None
    try:
        conn = get_connection()
        for species in TARGET_SPECIES:
            counts = sync_species(conn, species)
            for k in total: total[k] += counts.get(k, 0)
        log_sync(conn, total)
        conn.close()
    except Exception as e:
        error_msg = str(e)
        print(f"\n[FATAL ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
    print("\n" + "=" * 52)
    print(f"Fetched: {total['fetched']} | Inserted: {total['inserted']} | Skipped: {total['skipped']}")
    if error_msg: print(f"Fatal: {error_msg}")
    print("=" * 52)


if __name__ == "__main__":
    run()
