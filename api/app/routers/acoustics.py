from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import get_connection

router = APIRouter(prefix="/acoustics", tags=["Acoustics"])


@router.get("/")
def get_acoustics(
    species:   Optional[str] = Query(None, description="Filter by common name"),
    from_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    to_date:   Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    call_type: Optional[str] = Query(None, description="song / contact / click / unknown"),
    limit:     int = Query(2000, le=10000),
):
    """
    Returns whale acoustic detection records.
    Detected via underwater hydrophones — not visual sightings.
    Source: NOAA PACM (Passive Acoustic Cetacean Map).
    """
    try:
        conn = get_connection()
        cur  = conn.cursor()

        conditions, params = [], []

        if species:
            conditions.append("common_name = %s")
            params.append(species)
        if from_date:
            conditions.append("detected_on >= %s")
            params.append(from_date)
        if to_date:
            conditions.append("detected_on <= %s")
            params.append(to_date)
        if call_type:
            conditions.append("call_type = %s")
            params.append(call_type)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)

        cur.execute(f"""
            SELECT
                id,
                common_name,
                scientific_name,
                ST_X(location::geometry) AS longitude,
                ST_Y(location::geometry) AS latitude,
                detected_on,
                call_type,
                confidence,
                platform,
                region,
                source,
                source_url
            FROM acoustics
            {where}
            ORDER BY detected_on DESC NULLS LAST
            LIMIT %s;
        """, params)

        data = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "data":  data,
            "count": len(data),
            "layer": "acoustics",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
def get_acoustics_summary():
    """Returns acoustic detection count per species."""
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT common_name, COUNT(*) AS count,
                   MIN(detected_on) AS earliest,
                   MAX(detected_on) AS latest
            FROM acoustics
            GROUP BY common_name
            ORDER BY count DESC;
        """)
        data = cur.fetchall()
        cur.close()
        conn.close()
        return {"data": data, "layer": "acoustics"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
