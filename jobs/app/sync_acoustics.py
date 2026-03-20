"""
sync_acoustics.py

Fetches whale acoustic detection records from NOAA PACM
(Passive Acoustic Cetacean Map).

NOAA PACM API: https://pacm.fisheries.noaa.gov/
Provides detections from bottom-mounted hydrophones and buoys.

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

# ── Config ────────────────────────────────────────────────────

DEBUG     = "--debug" in sys.argv
LIMIT_ARG = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--limit=")), None)
MAX_RECORDS = LIMIT_ARG or 2000

PACM_API = "https://pacm.fisheries.noaa.gov/api/v1"

# PACM species codes
TARGET_SPECIES = [
    {"code": "Mn",  "common_name": "Humpback whale", "scientific_name": "Megaptera novaeangliae"},
    {"code": "Bm",  "common_name": "Blue whale",     "scientific_name": "Balaenoptera musculus"},
    {"code": "Bp",  "common_name": "Fin whale",      "scientific_name": "Balaenoptera physalus"},
    {"code": "Pm",  "common_name": "Sperm whale",    "scientific_name": "Physeter macrocephalus"},
    {"code": "Oo",  "common_name": "Orca",           "scientific_name": "Orcinus orca"},
]


def log(msg, force=False):
    if DEBUG or force:
        print(msg, flush=True)


def fetch_pacm(species_code: str, page: int = 1) -> dict:
    """Fetch acoustic detections from NOAA PACM API."""
    params = {
        "species": species_code,
        "page":    page,
        "limit":   100,
    }
    url = f"{PACM_API}/detections?" + urllib.parse.urlencode(params)
    log(f"  Fetching: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "whaledata.org/1.0 (research)", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        log(f"  [HTTP ERROR] {e.code} — {e.reason}", force=True)
        return {}
    except Exception as e:
        log(f"  [ERROR] {e}", force=True)
        return {}


def fetch_pacm_obis_fallback(aphia_id: int, offset: int) -> list:
    """
    Fallback: fetch acoustic records from OBIS when PACM API is unavailable.
    OBIS indexes some PACM data under acoustic datasets.
    """
    params = {
        "taxonid":  aphia_id,
        "hascoords": "true",
        "size":     200,
        "after":    offset,
        "datasetid": "ce2de8dc-93ca-4003-bad3-46c20f640f8c",  # NOAA PACM OBIS dataset
        "fields":   "id,decimalLongitude,decimalLatitude,eventDate,locality,datasetName",
    }
    url = "https://api.obis.org/v3/occurrence?" + urllib.parse.urlencode(params)
    log(f"  [FALLBACK] Fetching from OBIS: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "whaledata.org/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            return data.get("results", [])
    except Exception as e:
        log(f"  [FALLBACK ERROR] {e}", force=True)
        return []


APHIA_IDS = {
    "Mn": 137091,
    "Bm": 137090,
    "Bp": 137092,
    "Pm": 137102,
    "Oo": 137083,
}


def insert_acoustic(conn, record: dict, common_name: str, scientific_name: str, source_prefix: str = "pacm") -> str:
    cur = conn.cursor()
    try:
        source_id = str(record.get("id", ""))
        lat = record.get("decimalLatitude") or record.get("latitude")
        lng = record.get("decimalLongitude") or record.get("longitude")

        if not source_id or lat is None or lng is None:
            return "skipped"

        detected_on = str(record.get("eventDate") or record.get("date") or "")[:10] or None
        call_type   = record.get("call_type") or record.get("callType") or "unknown"
        confidence  = record.get("confidence") or "unknown"
        platform    = record.get("locality") or record.get("platform") or record.get("datasetName") or ""
        region      = record.get("region") or record.get("locality") or ""

        cur.execute("""
            INSERT INTO acoustics (
                common_name, scientific_name, location, detected_on,
                call_type, confidence, platform, region,
                source, source_id, source_url
            ) VALUES (
                %s, %s,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s, %s, %s, %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (source, source_id) DO NOTHING;
        """, (
            common_name, scientific_name,
            float(lng), float(lat),
            detected_on, call_type, confidence, platform, region,
            source_prefix, source_id,
            f"https://pacm.fisheries.noaa.gov/detections/{source_id}"
        ))
        conn.commit()
        result = "inserted" if cur.rowcount > 0 else "skipped"
        log(f"  [{result.upper()}] {common_name} acoustic @ {lat:.2f},{lng:.2f} on {detected_on}")
        return result

    except Exception as e:
        conn.rollback()
        log(f"  [ERROR] Insert failed: {e}", force=True)
        return "error"
    finally:
        cur.close()


def sync_species(conn, species: dict) -> dict:
    counts = {"fetched": 0, "inserted": 0, "skipped": 0, "error": 0}
    log(f"\n→ Syncing {species['common_name']} acoustics...", force=True)

    # Try PACM API first
    page = 1
    pacm_success = False

    while counts["fetched"] < MAX_RECORDS:
        data    = fetch_pacm(species["code"], page)
        records = data.get("data") or data.get("results") or []

        if records:
            pacm_success = True
            counts["fetched"] += len(records)
            log(f"  PACM page {page}: {len(records)} records")
            for r in records:
                result = insert_acoustic(conn, r, species["common_name"], species["scientific_name"], "pacm")
                counts[result] = counts.get(result, 0) + 1
            if len(records) < 100:
                break
            page += 1
        else:
            log(f"  PACM returned no data for {species['code']}", force=True)
            break

    # Fallback to OBIS if PACM returned nothing
    if not pacm_success:
        log(f"  Trying OBIS fallback for {species['common_name']}...", force=True)
        aphia_id = APHIA_IDS.get(species["code"])
        if aphia_id:
            offset = 0
            while counts["fetched"] < MAX_RECORDS:
                records = fetch_pacm_obis_fallback(aphia_id, offset)
                if not records:
                    break
                counts["fetched"] += len(records)
                for r in records:
                    result = insert_acoustic(conn, r, species["common_name"], species["scientific_name"], "pacm_obis")
                    counts[result] = counts.get(result, 0) + 1
                offset += len(records)
                if len(records) < 200:
                    break

    log(f"  Done — inserted: {counts['inserted']}, skipped: {counts['skipped']}", force=True)
    return counts


def log_sync(conn, total: dict, error_msg: str = None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sync_log (source, started_at, completed_at, records_fetched,
                              records_inserted, records_skipped, status, error_message)
        VALUES ('acoustics', NOW(), NOW(), %s, %s, %s, %s, %s);
    """, (total["fetched"], total["inserted"], total["skipped"],
          "failed" if error_msg else "success", error_msg))
    conn.commit()
    cur.close()


def run():
    print("=" * 52)
    print("whaledata — Acoustics sync (NOAA PACM)")
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
