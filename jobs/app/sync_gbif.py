"""
sync_gbif.py

Fetches whale sighting records from the GBIF API and writes them
into the sightings table. Logs each run to sync_log.

Targets the 6 key species for whaledata.org:
- Humpback whale
- Blue whale
- Orca (killer whale)
- Grey whale
- Sperm whale
- Fin whale

Usage:
    python -m app.sync_gbif
"""

import requests
import psycopg2
from datetime import datetime, date
from app.database import get_connection

# ----------------------------
# GBIF taxon keys for target species
# These are stable GBIF species IDs
# ----------------------------
TARGET_SPECIES = [
    {"taxon_key": 2440898, "common_name": "Humpback whale",   "scientific_name": "Megaptera novaeangliae"},
    {"taxon_key": 2440718, "common_name": "Blue whale",        "scientific_name": "Balaenoptera musculus"},
    {"taxon_key": 2440522, "common_name": "Orca",              "scientific_name": "Orcinus orca"},
    {"taxon_key": 2440714, "common_name": "Grey whale",        "scientific_name": "Eschrichtius robustus"},
    {"taxon_key": 2440764, "common_name": "Sperm whale",       "scientific_name": "Physeter macrocephalus"},
    {"taxon_key": 2440706, "common_name": "Fin whale",         "scientific_name": "Balaenoptera physalus"},
]

GBIF_API    = "https://api.gbif.org/v1/occurrence/search"
BATCH_SIZE  = 300
MAX_RECORDS = 1000  # max per species per run — increase later if needed


def start_sync_log(conn, source: str) -> int:
    """Insert a sync_log row and return its ID."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sync_log (source, started_at, status)
        VALUES (%s, %s, 'running')
        RETURNING id;
    """, (source, datetime.now()))
    log_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return log_id


def finish_sync_log(conn, log_id: int, fetched: int, inserted: int, updated: int, skipped: int, error: str = None):
    """Update the sync_log row when the job finishes."""
    cur = conn.cursor()
    cur.execute("""
        UPDATE sync_log SET
            completed_at    = %s,
            records_fetched  = %s,
            records_inserted = %s,
            records_updated  = %s,
            records_skipped  = %s,
            status           = %s,
            error_message    = %s
        WHERE id = %s;
    """, (
        datetime.now(),
        fetched,
        inserted,
        updated,
        skipped,
        "failed" if error else "success",
        error,
        log_id
    ))
    conn.commit()
    cur.close()


def fetch_gbif_page(taxon_key: int, offset: int) -> list:
    """Fetch one page of GBIF occurrences for a taxon."""
    params = {
        "taxonKey":      taxon_key,
        "hasCoordinate": "true",
        "occurrenceStatus": "PRESENT",
        "limit":         BATCH_SIZE,
        "offset":        offset,
    }
    response = requests.get(GBIF_API, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("results", [])


def upsert_sighting(cur, record: dict, common_name: str) -> str:
    """
    Insert a sighting record. Returns 'inserted', 'skipped', or 'error'.
    Duplicate source+source_id combinations are silently skipped.
    """
    try:
        source_id   = str(record.get("key", ""))
        sci_name    = record.get("species") or record.get("scientificName", "")
        lat         = record.get("decimalLatitude")
        lng         = record.get("decimalLongitude")
        sighted_on  = record.get("eventDate", "")[:10] if record.get("eventDate") else None
        region      = record.get("country") or record.get("countryCode") or "Unknown"
        source_url  = f"https://www.gbif.org/occurrence/{source_id}"

        if not (sci_name and lat and lng and source_id):
            return "skipped"

        # Parse date safely
        try:
            sighted_date = date.fromisoformat(sighted_on) if sighted_on else None
        except ValueError:
            sighted_date = None

        cur.execute("""
            INSERT INTO sightings (
                scientific_name,
                common_name,
                location,
                sighted_on,
                region,
                source,
                source_id,
                source_url,
                individual_count,
                verified
            ) VALUES (
                %s, %s,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s, %s, 'gbif', %s, %s, 1, false
            )
            ON CONFLICT (source, source_id) DO NOTHING;
        """, (
            sci_name,
            common_name,
            lng, lat,
            sighted_date,
            region,
            source_id,
            source_url,
        ))

        return "inserted" if cur.rowcount > 0 else "skipped"

    except Exception as e:
        print(f"  [error] Failed to insert record: {e}")
        return "error"


def sync_species(conn, species: dict) -> dict:
    """Sync all sightings for one species. Returns counts."""
    taxon_key   = species["taxon_key"]
    common_name = species["common_name"]
    sci_name    = species["scientific_name"]

    print(f"\n→ Syncing {common_name} ({sci_name})")

    counts = {"fetched": 0, "inserted": 0, "skipped": 0}
    offset = 0

    while counts["fetched"] < MAX_RECORDS:
        records = fetch_gbif_page(taxon_key, offset)
        if not records:
            break

        cur = conn.cursor()
        for record in records:
            result = upsert_sighting(cur, record, common_name)
            counts["fetched"] += 1
            if result == "inserted":
                counts["inserted"] += 1
            else:
                counts["skipped"] += 1

        conn.commit()
        cur.close()

        print(f"  Batch offset {offset}: {len(records)} records — {counts['inserted']} inserted so far")
        offset += BATCH_SIZE

        if len(records) < BATCH_SIZE:
            break  # no more pages

    return counts


def run():
    """Main entry point for the GBIF sync job."""
    print("=" * 50)
    print("whaledata — GBIF sync job")
    print(f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    conn    = get_connection()
    log_id  = start_sync_log(conn, "gbif")

    total   = {"fetched": 0, "inserted": 0, "updated": 0, "skipped": 0}
    error   = None

    try:
        for species in TARGET_SPECIES:
            counts = sync_species(conn, species)
            total["fetched"]  += counts["fetched"]
            total["inserted"] += counts["inserted"]
            total["skipped"]  += counts["skipped"]

    except Exception as e:
        error = str(e)
        print(f"\n[FATAL ERROR] {error}")

    finally:
        finish_sync_log(
            conn, log_id,
            fetched  = total["fetched"],
            inserted = total["inserted"],
            updated  = total["updated"],
            skipped  = total["skipped"],
            error    = error
        )
        conn.close()

    print("\n" + "=" * 50)
    print("Sync complete")
    print(f"  Fetched:  {total['fetched']}")
    print(f"  Inserted: {total['inserted']}")
    print(f"  Skipped:  {total['skipped']}")
    if error:
        print(f"  Error:    {error}")
    print("=" * 50)


if __name__ == "__main__":
    run()
