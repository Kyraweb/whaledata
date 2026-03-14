"""
sync_obis.py

Fetches Fin whale sightings from OBIS (Ocean Biodiversity Information System)
to supplement the sparse GBIF data for Balaenoptera physalus.

OBIS API docs: https://api.obis.org/v3
"""

from app.database import get_connection
from datetime import datetime

OBIS_API = "https://api.obis.org/v3"
FIN_WHALE_APHIA_ID = 137092  # WoRMS AphiaID for Balaenoptera physalus
BATCH_SIZE = 1000
MAX_RECORDS = 1200

def fetch_obis_page(offset: int) -> dict:
    import urllib.request
    import json
    url = (
        f"{OBIS_API}/occurrence"
        f"?taxonid={FIN_WHALE_APHIA_ID}"
        f"&hascoords=true"
        f"&size={BATCH_SIZE}"
        f"&after={offset}"
        f"&fields=id,decimalLongitude,decimalLatitude,eventDate,country,depth,datasetName"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "whaledata.org/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  [error] OBIS fetch failed: {e}")
        return {}


def insert_sighting(conn, record: dict) -> str:
    cur = conn.cursor()
    try:
        source_id = str(record.get("id", ""))
        lat = record.get("decimalLatitude")
        lng = record.get("decimalLongitude")

        if not (source_id and lat is not None and lng is not None):
            return "skipped"

        # Parse date
        raw_date = record.get("eventDate", "")
        try:
            if raw_date:
                sighted_date = raw_date[:10]
            else:
                sighted_date = None
        except Exception:
            sighted_date = None

        region = record.get("country") or record.get("datasetName") or ""
        source_url = f"https://obis.org/occurrence/{source_id}"

        cur.execute("""
            INSERT INTO sightings (
                scientific_name, common_name,
                location, sighted_on, region,
                source, source_id, source_url,
                individual_count, verified
            ) VALUES (
                %s, %s,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s, %s, 'obis', %s, %s, 1, false
            )
            ON CONFLICT (source, source_id) DO NOTHING;
        """, (
            "Balaenoptera physalus", "Fin whale",
            lng, lat,
            sighted_date, region,
            source_id, source_url,
        ))
        conn.commit()
        return "inserted" if cur.rowcount > 0 else "skipped"

    except Exception as e:
        conn.rollback()
        print(f"  [error] Insert failed: {e}")
        return "error"
    finally:
        cur.close()


def run():
    print("=" * 50)
    print("whaledata — OBIS Fin whale sync")
    print(f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    conn = get_connection()
    inserted = 0
    skipped  = 0
    offset   = 0

    while inserted + skipped < MAX_RECORDS:
        print(f"  Fetching offset {offset}...")
        data = fetch_obis_page(offset)
        records = data.get("results", [])

        if not records:
            print("  No more records.")
            break

        for record in records:
            result = insert_sighting(conn, record)
            if result == "inserted":
                inserted += 1
            else:
                skipped += 1

        print(f"  Batch: {len(records)} records — {inserted} inserted so far")
        offset += len(records)

        if len(records) < BATCH_SIZE:
            break

    conn.close()
    print("\n" + "=" * 50)
    print(f"Done — {inserted} inserted, {skipped} skipped")
    print("=" * 50)


if __name__ == "__main__":
    run()
