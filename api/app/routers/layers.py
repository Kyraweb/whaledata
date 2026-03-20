from fastapi import APIRouter, HTTPException
from app.database import get_connection

router = APIRouter(prefix="/layers", tags=["Layers"])


@router.get("/summary")
def get_layers_summary():
    """
    Returns record counts for ALL data layers in a single request.
    Used by the frontend to populate the layers panel without
    making 4 separate API calls.

    Returns per-layer, per-species counts so the UI can show
    how many records exist for each species in each data source.
    """
    try:
        conn = get_connection()
        cur  = conn.cursor()

        # Sightings (GBIF + OBIS)
        cur.execute("""
            SELECT common_name, source, COUNT(*) AS count
            FROM sightings
            GROUP BY common_name, source
            ORDER BY common_name, source;
        """)
        sightings = cur.fetchall()

        # Strandings
        cur.execute("""
            SELECT common_name, COUNT(*) AS count
            FROM strandings
            GROUP BY common_name ORDER BY common_name;
        """)
        strandings = cur.fetchall()

        # Acoustics
        cur.execute("""
            SELECT common_name, COUNT(*) AS count
            FROM acoustics
            GROUP BY common_name ORDER BY common_name;
        """)
        acoustics = cur.fetchall()

        # iNaturalist
        cur.execute("""
            SELECT common_name, COUNT(*) AS count
            FROM inaturalist_sightings
            GROUP BY common_name ORDER BY common_name;
        """)
        inaturalist = cur.fetchall()

        # Historical
        cur.execute("""
            SELECT common_name, COUNT(*) AS count
            FROM historical_sightings
            GROUP BY common_name ORDER BY common_name;
        """)
        historical = cur.fetchall()

        cur.close()
        conn.close()

        return {
            "layers": {
                "sightings":   {"data": sightings,   "total": sum(r["count"] for r in sightings)},
                "strandings":  {"data": strandings,  "total": sum(r["count"] for r in strandings)},
                "acoustics":   {"data": acoustics,   "total": sum(r["count"] for r in acoustics)},
                "inaturalist": {"data": inaturalist, "total": sum(r["count"] for r in inaturalist)},
                "historical":  {"data": historical,  "total": sum(r["count"] for r in historical)},
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
