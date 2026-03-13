from fastapi import APIRouter, HTTPException
from app.database import get_connection

router = APIRouter(prefix="/routes", tags=["Migration Routes"])


@router.get("/")
def get_migration_routes():
    """
    Returns all migration routes with their GeoJSON linestring coordinates.
    Used to render animated paths on the globe.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                mr.id,
                mr.name,
                s.common_name,
                s.scientific_name,
                mr.season,
                mr.direction,
                mr.origin_region,
                mr.destination_region,
                mr.distance_km,
                mr.description,
                ST_AsGeoJSON(mr.route::geometry) AS geojson
            FROM migration_routes mr
            JOIN species s ON s.id = mr.species_id
            ORDER BY s.common_name, mr.name;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Parse the geojson string into a proper object
        import json
        routes = []
        for row in rows:
            r = dict(row)
            if r.get('geojson'):
                r['geojson'] = json.loads(r['geojson'])
            routes.append(r)

        return {"data": routes, "count": len(routes)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
