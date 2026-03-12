from fastapi import APIRouter, HTTPException
from app.database import get_connection

router = APIRouter(prefix="/species", tags=["Species"])


@router.get("/")
def get_all_species():
    """
    Returns all whale species from the database.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                id,
                scientific_name,
                common_name,
                family,
                conservation_status,
                population_trend,
                description,
                average_length_m,
                average_weight_kg,
                image_url,
                sound_url,
                iucn_url,
                wikipedia_url
            FROM species
            ORDER BY common_name ASC;
        """)
        data = cur.fetchall()
        cur.close()
        conn.close()
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{species_id}")
def get_species_by_id(species_id: int):
    """
    Returns a single species by its ID.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                id,
                scientific_name,
                common_name,
                family,
                conservation_status,
                population_trend,
                description,
                average_length_m,
                average_weight_kg,
                image_url,
                sound_url,
                iucn_url,
                wikipedia_url
            FROM species
            WHERE id = %s;
        """, (species_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Species not found")
        return {"data": row}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
