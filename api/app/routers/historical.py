from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import get_connection

router = APIRouter(prefix="/historical", tags=["Historical"])


@router.get("/")
def get_historical(
    species:  Optional[str] = Query(None, description="Filter by common name"),
    from_year: Optional[int] = Query(None, description="Start year e.g. 1800"),
    to_year:   Optional[int] = Query(None, description="End year e.g. 1950"),
    limit:    int = Query(2000, le=10000),
):
    """
    Returns pre-1950 whale sighting records from digitised whaling logs
    and historical surveys. Source: GBIF historical datasets.
    """
    try:
        conn = get_connection()
        cur  = conn.cursor()

        conditions, params = [], []

        if species:
            conditions.append("common_name = %s")
            params.append(species)
        if from_year:
            conditions.append("year >= %s")
            params.append(from_year)
        if to_year:
            conditions.append("year <= %s")
            params.append(to_year)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)

        cur.execute(f"""
            SELECT
                id,
                common_name,
                scientific_name,
                ST_X(location::geometry) AS longitude,
                ST_Y(location::geometry) AS latitude,
                sighted_on,
                year,
                vessel,
                region,
                source,
                source_url
            FROM historical_sightings
            {where}
            ORDER BY year DESC NULLS LAST
            LIMIT %s;
        """, params)

        data = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "data":  data,
            "count": len(data),
            "layer": "historical",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
def get_historical_summary():
    """Returns historical record count per species with year ranges."""
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT common_name, COUNT(*) AS count,
                   MIN(year) AS earliest_year,
                   MAX(year) AS latest_year
            FROM historical_sightings
            GROUP BY common_name
            ORDER BY count DESC;
        """)
        data = cur.fetchall()
        cur.close()
        conn.close()
        return {"data": data, "layer": "historical"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
