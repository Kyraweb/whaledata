# whaledata.org — Database Guide

This document covers the database schema, how to set it up from scratch, how the tables relate, and useful queries for exploring the data.

---

## Quick setup

```bash
# Apply the full schema (creates all 11 tables)
psql -U whaledata_user -d whaledata -f api/schema_full.sql

# Verify tables were created
psql -U whaledata_user -d whaledata -c "\dt"
```

You should see:

```
 alert_subscribers
 acoustics
 historical_sightings
 inaturalist_sightings
 migration_routes
 population_estimates
 regions
 sightings
 species
 strandings
 sync_log
```

---

## Table overview

### `species`
The master list of 6 whale species. All other tables reference this via `common_name` or `species_id`.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial | Primary key |
| `common_name` | varchar | e.g. `Humpback whale` |
| `scientific_name` | varchar | e.g. `Megaptera novaeangliae` |
| `conservation_status` | varchar | IUCN code: LC, NT, VU, EN, CR, DD |
| `population_trend` | varchar | increasing / decreasing / stable / unknown |

### `sightings`
Visual whale sighting records from GBIF and OBIS. The primary data layer.

| Column | Type | Description |
|--------|------|-------------|
| `location` | geography(POINT) | PostGIS point — stored as (longitude, latitude) |
| `sighted_on` | date | Date of observation |
| `source` | varchar | `gbif` or `obis` |
| `source_id` | varchar | Original record ID from the source |

### `strandings`
Whale stranding events — animals found dead or alive on beaches/shores. Source: NOAA via OBIS.

| Column | Type | Description |
|--------|------|-------------|
| `condition` | varchar | `alive`, `dead`, or `unknown` |
| `stranded_on` | date | Date found |
| `country` | varchar | Country where stranding occurred |

### `acoustics`
Underwater acoustic detections from hydrophone networks. Whales heard but not seen. Source: NOAA PACM via OBIS.

| Column | Type | Description |
|--------|------|-------------|
| `call_type` | varchar | `song`, `contact`, `click`, or `unknown` |
| `platform` | varchar | Name of the hydrophone platform |

### `inaturalist_sightings`
Research-grade citizen science observations from iNaturalist.org. Community-verified records only.

| Column | Type | Description |
|--------|------|-------------|
| `quality_grade` | varchar | `research` (only synced), `needs_id`, `casual` |
| `observer` | varchar | iNaturalist username |
| `image_url` | text | Photo URL if available |

### `historical_sightings`
Pre-1950 records from digitised 19th and early 20th century whaling logs. Source: GBIF historical datasets.

| Column | Type | Description |
|--------|------|-------------|
| `year` | integer | Year only (when full date is unknown) |
| `vessel` | varchar | Whaling ship name if recorded |

### `migration_routes`
Known seasonal migration corridors. These are the animated arcs on the globe.

| Column | Type | Description |
|--------|------|-------------|
| `route` | geography(LINESTRING) | PostGIS linestring of the route path |
| `season` | varchar | `summer`, `winter`, or `year-round` |
| `direction` | varchar | `northbound`, `southbound`, or `circular` |

### `sync_log`
Tracks every data sync job. Used by the admin panel Sync Logs page.

| Column | Type | Description |
|--------|------|-------------|
| `source` | varchar | Which sync ran: `gbif`, `obis`, `strandings`, etc. |
| `status` | varchar | `running`, `success`, or `failed` |
| `records_inserted` | integer | New records added |
| `records_skipped` | integer | Duplicates skipped via `ON CONFLICT DO NOTHING` |

### `alert_subscribers`
Weekly email digest subscribers. Managed via the admin panel.

| Column | Type | Description |
|--------|------|-------------|
| `token` | varchar | Used for confirm and unsubscribe links |
| `confirmed` | boolean | Must be `true` for emails to send |
| `species_filter` | varchar | NULL = all species |
| `layer_filter` | varchar | NULL = all layers |

---

## How coordinates work

All location data uses **PostGIS geography** type with SRID 4326 (WGS84 — same as GPS).

Coordinates are stored as `ST_MakePoint(longitude, latitude)` — **longitude first**.

To query locations:
```sql
-- Get longitude and latitude from a sighting
SELECT
  ST_X(location::geometry) AS longitude,
  ST_Y(location::geometry) AS latitude
FROM sightings
LIMIT 5;

-- Find sightings within 500km of a point
SELECT common_name, sighted_on
FROM sightings
WHERE ST_DWithin(
  location,
  ST_MakePoint(-157.8, 21.3)::geography,
  500000  -- metres
);
```

---

## Seeding species data

After applying the schema, seed the 6 species manually or via the admin panel. Example:

```sql
INSERT INTO species (scientific_name, common_name, conservation_status, population_trend, description) VALUES
('Megaptera novaeangliae', 'Humpback whale', 'LC', 'increasing',
 'Famous for their haunting songs. Makes one of the longest migrations of any mammal.'),
('Balaenoptera musculus',  'Blue whale',     'EN', 'increasing',
 'The largest animal ever known to have existed on Earth.'),
('Eschrichtius robustus',  'Grey whale',     'LC', 'stable',
 'Undertakes the longest migration of any mammal — up to 20,000 km round trip.'),
('Physeter macrocephalus', 'Sperm whale',    'VU', 'unknown',
 'The largest toothed predator on Earth. Capable of diving to 3,000m.'),
('Balaenoptera physalus',  'Fin whale',      'VU', 'increasing',
 'The second largest animal on Earth, known as the greyhound of the sea.'),
('Orcinus orca',           'Orca',           'DD', 'unknown',
 'The apex predator of the ocean, found in every sea from Arctic to Antarctic.');
```

---

## Running the sync scripts

After seeding species, populate the data tables:

```bash
# From the jobs/ service terminal in Coolify
python -m app.sync_gbif           # ~2 min — GBIF sightings for all 6 species
python -m app.sync_obis           # ~1 min — OBIS Fin whale supplement
python -m app.sync_strandings     # ~3 min — NOAA stranding events
python -m app.sync_inaturalist    # ~2 min — iNaturalist observations
python -m app.sync_historical     # ~1 min — Pre-1950 whaling records
python -m app.sync_acoustics      # ~1 min — Hydrophone detections

# All scripts support --debug flag for verbose output
python -m app.sync_gbif --debug

# And --limit=N to cap records for testing
python -m app.sync_gbif --limit=100
```

---

## Useful queries

```sql
-- Total records per layer
SELECT 'sightings' AS layer, COUNT(*) FROM sightings
UNION ALL SELECT 'strandings', COUNT(*) FROM strandings
UNION ALL SELECT 'acoustics', COUNT(*) FROM acoustics
UNION ALL SELECT 'inaturalist', COUNT(*) FROM inaturalist_sightings
UNION ALL SELECT 'historical', COUNT(*) FROM historical_sightings;

-- Sightings per species
SELECT common_name, source, COUNT(*) AS count
FROM sightings
GROUP BY common_name, source
ORDER BY common_name, source;

-- Most recent strandings
SELECT common_name, stranded_on, condition, region, country
FROM strandings
ORDER BY stranded_on DESC NULLS LAST
LIMIT 20;

-- Subscriber count
SELECT confirmed, COUNT(*) FROM alert_subscribers GROUP BY confirmed;

-- Last sync per source
SELECT source, status, completed_at, records_inserted
FROM sync_log
WHERE id IN (
  SELECT MAX(id) FROM sync_log GROUP BY source
)
ORDER BY source;

-- Database size
SELECT pg_size_pretty(pg_database_size(current_database()));
```

---

## GBIF Taxon Keys

Used by `sync_gbif.py` to query the GBIF API:

| Species | Common Name | Taxon Key |
|---------|-------------|-----------|
| *Megaptera novaeangliae* | Humpback whale | 2440898 |
| *Balaenoptera musculus* | Blue whale | 2440718 |
| *Orcinus orca* | Orca | 2440483 |
| *Eschrichtius robustus* | Grey whale | 2440714 |
| *Physeter macrocephalus* | Sperm whale | 2440764 |
| *Balaenoptera physalus* | Fin whale | 2440706 |

## iNaturalist Taxon IDs

Used by `sync_inaturalist.py`:

| Species | Taxon ID |
|---------|----------|
| Humpback whale | 41472 |
| Blue whale | 41467 |
| Fin whale | 41468 |
| Grey whale | 41476 |
| Sperm whale | 41490 |
| Orca | 41446 |

## OBIS AphiaIDs (WoRMS)

Used by `sync_obis.py` and `sync_strandings.py`:

| Species | AphiaID |
|---------|---------|
| Humpback whale | 137091 |
| Blue whale | 137090 |
| Fin whale | 137092 |
| Sperm whale | 137102 |
| Grey whale | 137098 |
| Orca | 137083 |
