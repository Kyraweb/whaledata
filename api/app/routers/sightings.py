from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import get_connection

router = APIRouter(prefix="/sightings", tags=["Sightings"])


@router.get("/")
def get_sightings(
    species: Optional[str] = Query(None, description="Filter by common name e.g. 'Humpback whale'"),
    from_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    limit: int = Query(5000, le=10000, description="Max records to return"),
):
    """
    Returns whale sightings with coordinates.
    Designed to feed directly into Deck.gl on the frontend.

    Each record includes:
    - longitude, latitude (for map rendering)
    - common_name, scientific_name
    - sighted_on, region, source
    """
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Build query dynamically based on filters
        conditions = []
        params = []

        if species:
            conditions.append("common_name = %s")
            params.append(species)

        if from_date:
            conditions.append("sighted_on >= %s")
            params.append(from_date)

        if to_date:
            conditions.append("sighted_on <= %s")
            params.append(to_date)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        params.append(limit)

        cur.execute(f"""
            SELECT
                id,
                common_name,
                scientific_name,
                ST_X(location::geometry) AS longitude,
                ST_Y(location::geometry) AS latitude,
                sighted_on,
                region,
                source,
                source_url,
                individual_count
            FROM sightings
            {where_clause}
            ORDER BY sighted_on DESC NULLS LAST
            LIMIT %s;
        """, params)

        data = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "data": data,
            "count": len(data),
            "filters": {
                "species": species,
                "from_date": from_date,
                "to_date": to_date,
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/species-summary")
def get_species_summary():
    """
    Returns a count of sightings per species.
    Used to populate the species filter on the frontend.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                common_name,
                scientific_name,
                COUNT(*) AS sighting_count,
                MIN(sighted_on) AS earliest,
                MAX(sighted_on) AS latest
            FROM sightings
            GROUP BY common_name, scientific_name
            ORDER BY sighting_count DESC;
        """)
        data = cur.fetchall()
        cur.close()
        conn.close()
        return {"data": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
