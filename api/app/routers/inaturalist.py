from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import get_connection

router = APIRouter(prefix="/inaturalist", tags=["iNaturalist"])


@router.get("/")
def get_inaturalist(
    species:       Optional[str] = Query(None, description="Filter by common name"),
    from_date:     Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    to_date:       Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    quality_grade: Optional[str] = Query(None, description="research / needs_id / casual"),
    limit:         int = Query(2000, le=10000),
):
    """
    Returns citizen science whale sightings from iNaturalist.
    Only research-grade observations are synced by default.
    Source: iNaturalist.org
    """
    try:
        conn = get_connection()
        cur  = conn.cursor()

        conditions, params = [], []

        if species:
            conditions.append("common_name = %s")
            params.append(species)
        if from_date:
            conditions.append("observed_on >= %s")
            params.append(from_date)
        if to_date:
            conditions.append("observed_on <= %s")
            params.append(to_date)
        if quality_grade:
            conditions.append("quality_grade = %s")
            params.append(quality_grade)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)

        cur.execute(f"""
            SELECT
                id,
                common_name,
                scientific_name,
                ST_X(location::geometry) AS longitude,
                ST_Y(location::geometry) AS latitude,
                observed_on,
                quality_grade,
                region,
                source_id,
                source_url,
                image_url,
                observer
            FROM inaturalist_sightings
            {where}
            ORDER BY observed_on DESC NULLS LAST
            LIMIT %s;
        """, params)

        data = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "data":  data,
            "count": len(data),
            "layer": "inaturalist",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
def get_inaturalist_summary():
    """Returns iNaturalist observation count per species."""
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT common_name, COUNT(*) AS count,
                   MIN(observed_on) AS earliest,
                   MAX(observed_on) AS latest
            FROM inaturalist_sightings
            GROUP BY common_name
            ORDER BY count DESC;
        """)
        data = cur.fetchall()
        cur.close()
        conn.close()
        return {"data": data, "layer": "inaturalist"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
