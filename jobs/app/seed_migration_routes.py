"""
seed_migration_routes.py

Inserts known whale migration corridors into the migration_routes table.
Routes are based on published scientific literature and NOAA data.
Run once to populate the database.

Usage:
    python -m app.seed_migration_routes
"""

from app.database import get_connection
from datetime import datetime
import json

ROUTES = [
    # ─── HUMPBACK WHALE ───────────────────────────────────────────
    {
        "species_scientific": "Megaptera novaeangliae",
        "name": "North Pacific — Hawaii to Alaska",
        "season": "summer",
        "direction": "northbound",
        "origin_region": "Hawaii",
        "destination_region": "Gulf of Alaska",
        "distance_km": 5000,
        "description": "Humpbacks winter in warm Hawaiian waters to breed and calve, then migrate north to rich Alaskan feeding grounds each summer. One of the best-studied migrations in the world.",
        "coordinates": [
            [-158.0, 21.0],
            [-155.0, 25.0],
            [-152.0, 30.0],
            [-148.0, 38.0],
            [-143.0, 46.0],
            [-140.0, 52.0],
            [-148.0, 57.0],
            [-152.0, 58.5],
        ]
    },
    {
        "species_scientific": "Megaptera novaeangliae",
        "name": "South Atlantic — Brazil to Antarctica",
        "season": "summer",
        "direction": "southbound",
        "origin_region": "Abrolhos Bank, Brazil",
        "destination_region": "Antarctic Peninsula",
        "distance_km": 8500,
        "description": "Humpbacks from the Abrolhos breeding ground undertake one of the longest migrations of any mammal, travelling to Antarctic feeding grounds in the austral summer.",
        "coordinates": [
            [-38.5, -17.0],
            [-40.0, -25.0],
            [-42.0, -35.0],
            [-44.0, -45.0],
            [-48.0, -55.0],
            [-52.0, -62.0],
            [-55.0, -65.0],
        ]
    },

    # ─── GREY WHALE ───────────────────────────────────────────────
    {
        "species_scientific": "Eschrichtius robustus",
        "name": "Eastern Pacific — Baja to Arctic Alaska",
        "season": "summer",
        "direction": "northbound",
        "origin_region": "Baja California, Mexico",
        "destination_region": "Chukchi Sea, Alaska",
        "distance_km": 10000,
        "description": "The Eastern Pacific grey whale makes the longest annual migration of any mammal — from warm Mexican lagoons where they breed to Arctic feeding grounds. The population has recovered from near-extinction.",
        "coordinates": [
            [-114.0, 28.0],
            [-116.0, 32.0],
            [-119.0, 36.0],
            [-122.0, 38.0],
            [-124.0, 43.0],
            [-124.5, 48.0],
            [-126.0, 52.0],
            [-158.0, 58.0],
            [-163.0, 62.0],
            [-168.0, 65.5],
            [-166.0, 68.0],
        ]
    },

    # ─── BLUE WHALE ───────────────────────────────────────────────
    {
        "species_scientific": "Balaenoptera musculus",
        "name": "North Pacific — California to Costa Rica Dome",
        "season": "winter",
        "direction": "southbound",
        "origin_region": "California Coast",
        "destination_region": "Costa Rica Dome",
        "distance_km": 4000,
        "description": "Blue whales feed along the California coast in summer and autumn, then move south toward the highly productive Costa Rica Dome in winter. The largest animals ever to have lived on Earth.",
        "coordinates": [
            [-122.0, 36.0],
            [-120.0, 32.0],
            [-116.0, 28.0],
            [-112.0, 22.0],
            [-108.0, 14.0],
            [-90.0, 9.0],
        ]
    },
    {
        "species_scientific": "Balaenoptera musculus",
        "name": "Indian Ocean — Sri Lanka to Antarctic",
        "season": "summer",
        "direction": "southbound",
        "origin_region": "Sri Lanka",
        "destination_region": "Antarctic waters",
        "distance_km": 9000,
        "description": "A distinct pygmy blue whale population gathers off Sri Lanka before heading south to Antarctic feeding grounds. These animals are among the most acoustically active blue whales tracked.",
        "coordinates": [
            [82.0, 8.0],
            [80.0, 0.0],
            [75.0, -10.0],
            [70.0, -20.0],
            [65.0, -35.0],
            [60.0, -50.0],
            [55.0, -60.0],
        ]
    },

    # ─── SPERM WHALE ──────────────────────────────────────────────
    {
        "species_scientific": "Physeter macrocephalus",
        "name": "North Atlantic — Caribbean to deep water",
        "season": "year-round",
        "direction": "circular",
        "origin_region": "Caribbean Sea",
        "destination_region": "North Atlantic Deep Water",
        "distance_km": 3000,
        "description": "Female sperm whales and calves remain in warm tropical and subtropical waters year-round. Males migrate to higher latitudes to feed on giant squid in the deep ocean, returning to breed.",
        "coordinates": [
            [-65.0, 15.0],
            [-60.0, 20.0],
            [-55.0, 28.0],
            [-45.0, 35.0],
            [-35.0, 40.0],
            [-25.0, 45.0],
            [-20.0, 50.0],
        ]
    },

    # ─── FIN WHALE ────────────────────────────────────────────────
    {
        "species_scientific": "Balaenoptera physalus",
        "name": "North Atlantic — Caribbean to Iceland",
        "season": "summer",
        "direction": "northbound",
        "origin_region": "Caribbean and Gulf of Mexico",
        "destination_region": "Iceland and Norwegian Sea",
        "distance_km": 7000,
        "description": "Fin whales, the second largest animal on Earth, migrate from lower-latitude wintering grounds to productive subarctic feeding areas. Their low-frequency songs can travel thousands of kilometres.",
        "coordinates": [
            [-80.0, 25.0],
            [-72.0, 32.0],
            [-65.0, 38.0],
            [-50.0, 45.0],
            [-35.0, 52.0],
            [-22.0, 58.0],
            [-18.0, 64.0],
        ]
    },
]


def get_species_id(cur, scientific_name: str):
    cur.execute("SELECT id FROM species WHERE scientific_name = %s", (scientific_name,))
    row = cur.fetchone()
    return row[0] if row else None


def build_linestring(coordinates: list) -> str:
    """Build a WKT LINESTRING from a list of [lng, lat] pairs."""
    points = ", ".join(f"{lng} {lat}" for lng, lat in coordinates)
    return f"LINESTRING({points})"


def run():
    print("=" * 50)
    print("whaledata — Migration routes seed")
    print(f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    conn = get_connection()
    cur = conn.cursor()

    # First make sure species exist — insert them if not
    species_data = [
        ("Megaptera novaeangliae",  "Humpback whale",  "EN",  "increasing"),
        ("Eschrichtius robustus",   "Grey whale",      "LC",  "increasing"),
        ("Balaenoptera musculus",   "Blue whale",      "EN",  "increasing"),
        ("Physeter macrocephalus",  "Sperm whale",     "VU",  "unknown"),
        ("Balaenoptera physalus",   "Fin whale",       "VU",  "increasing"),
        ("Orcinus orca",            "Orca",            "DD",  "unknown"),
    ]

    for sci, common, status, trend in species_data:
        cur.execute("""
            INSERT INTO species (scientific_name, common_name, conservation_status, population_trend)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (scientific_name) DO NOTHING;
        """, (sci, common, status, trend))

    conn.commit()
    print("Species seeded.")

    # Insert migration routes
    inserted = 0
    skipped = 0

    for route in ROUTES:
        species_id = get_species_id(cur, route["species_scientific"])
        if not species_id:
            print(f"  [skip] Species not found: {route['species_scientific']}")
            skipped += 1
            continue

        linestring = build_linestring(route["coordinates"])

        cur.execute("""
            INSERT INTO migration_routes (
                species_id,
                name,
                route,
                season,
                direction,
                origin_region,
                destination_region,
                distance_km,
                description,
                source
            ) VALUES (
                %s, %s,
                ST_GeogFromText(%s),
                %s, %s, %s, %s, %s, %s,
                'NOAA / scientific literature'
            )
            ON CONFLICT DO NOTHING;
        """, (
            species_id,
            route["name"],
            linestring,
            route["season"],
            route["direction"],
            route["origin_region"],
            route["destination_region"],
            route["distance_km"],
            route["description"],
        ))

        print(f"  ✓ {route['name']}")
        inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print("\n" + "=" * 50)
    print(f"Done — {inserted} routes inserted, {skipped} skipped")
    print("=" * 50)


if __name__ == "__main__":
    run()
