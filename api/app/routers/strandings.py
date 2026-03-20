from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import get_connection

router = APIRouter(prefix="/strandings", tags=["Strandings"])


@router.get("/")
def get_strandings(
    species:   Optional[str] = Query(None, description="Filter by common name"),
    from_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    to_date:   Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    condition: Optional[str] = Query(None, description="alive / dead / unknown"),
    limit:     int = Query(2000, le=10000),
):
    """
    Returns whale stranding events with coordinates.
    Strandings are whales found dead or alive on beaches/shores.
    Source: NOAA / OBIS stranding datasets.
    """
    try:
        conn = get_connection()
        cur  = conn.cursor()

        conditions, params = [], []

        if species:
            conditions.append("common_name = %s")
            params.append(species)
        if from_date:
            conditions.append("stranded_on >= %s")
            params.append(from_date)
        if to_date:
            conditions.append("stranded_on <= %s")
            params.append(to_date)
        if condition:
            conditions.append("condition = %s")
            params.append(condition)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)

        cur.execute(f"""
            SELECT
                id,
                common_name,
                scientific_name,
                ST_X(location::geometry) AS longitude,
                ST_Y(location::geometry) AS latitude,
                stranded_on,
                condition,
                individual_count,
                region,
                country,
                source,
                source_url
            FROM strandings
            {where}
            ORDER BY stranded_on DESC NULLS LAST
            LIMIT %s;
        """, params)

        data = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "data":  data,
            "count": len(data),
            "layer": "strandings",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
def get_strandings_summary():
    """Returns stranding count per species."""
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT common_name, COUNT(*) AS count,
                   MIN(stranded_on) AS earliest,
                   MAX(stranded_on) AS latest
            FROM strandings
            GROUP BY common_name
            ORDER BY count DESC;
        """)
        data = cur.fetchall()
        cur.close()
        conn.close()
        return {"data": data, "layer": "strandings"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
