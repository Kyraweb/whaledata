-- ============================================================
-- whaledata.org — Database Schema
-- PostgreSQL + PostGIS
-- ============================================================

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- 1. SPECIES
-- Master list of whale species and their profile data
-- ============================================================
CREATE TABLE species (
    id                  SERIAL PRIMARY KEY,
    scientific_name     VARCHAR(255) NOT NULL UNIQUE,
    common_name         VARCHAR(255) NOT NULL,
    family              VARCHAR(255),                       -- e.g. Balaenopteridae
    conservation_status VARCHAR(10),                        -- IUCN codes: LC, NT, VU, EN, CR, EX
    population_trend    VARCHAR(20),                        -- increasing / decreasing / stable / unknown
    description         TEXT,
    average_length_m    DECIMAL(5,2),                       -- average length in metres
    average_weight_kg   DECIMAL(10,2),                      -- average weight in kg
    image_url           TEXT,
    sound_url           TEXT,                               -- whale song audio file
    iucn_url            TEXT,                               -- link to IUCN red list page
    wikipedia_url       TEXT,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 2. POPULATION ESTIMATES
-- Global or regional population estimates per species
-- Separate from sightings — these are scientific estimates
-- ============================================================
CREATE TABLE population_estimates (
    id                  SERIAL PRIMARY KEY,
    species_id          INTEGER NOT NULL REFERENCES species(id) ON DELETE CASCADE,
    region              VARCHAR(255),                       -- NULL means global estimate
    estimate_min        INTEGER,                            -- lower bound
    estimate_max        INTEGER,                            -- upper bound
    estimate_year       INTEGER,                            -- year of estimate
    source              VARCHAR(255),                       -- e.g. IUCN, NOAA
    source_url          TEXT,
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 3. SIGHTINGS
-- Individual whale sighting records from open data sources
-- ============================================================
CREATE TABLE sightings (
    id                  SERIAL PRIMARY KEY,
    species_id          INTEGER REFERENCES species(id) ON DELETE SET NULL,
    scientific_name     VARCHAR(255),                       -- kept for cases where species_id is null
    common_name         VARCHAR(255),
    location            GEOGRAPHY(POINT, 4326) NOT NULL,   -- PostGIS point (lng, lat)
    sighted_on          DATE,                              -- date of sighting
    region              VARCHAR(255),                       -- country or ocean region
    source              VARCHAR(50) NOT NULL,               -- gbif / obis / inaturalist
    source_id           VARCHAR(255),                       -- original record ID from source
    source_url          TEXT,                               -- link back to original record
    individual_count    INTEGER DEFAULT 1,
    verified            BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMP DEFAULT NOW(),
    UNIQUE (source, source_id)                             -- prevent duplicate imports
);

-- Index for spatial queries
CREATE INDEX sightings_location_idx ON sightings USING GIST (location);
-- Index for date filtering
CREATE INDEX sightings_sighted_on_idx ON sightings (sighted_on);
-- Index for species filtering
CREATE INDEX sightings_species_id_idx ON sightings (species_id);

-- ============================================================
-- 4. MIGRATION ROUTES
-- Known migration corridors per species
-- These are the animated arcs on the globe
-- ============================================================
CREATE TABLE migration_routes (
    id                  SERIAL PRIMARY KEY,
    species_id          INTEGER NOT NULL REFERENCES species(id) ON DELETE CASCADE,
    name                VARCHAR(255),                       -- e.g. "North Pacific Humpback Route"
    route               GEOGRAPHY(LINESTRING, 4326),        -- PostGIS linestring path
    season              VARCHAR(20),                        -- summer / winter / year-round
    direction           VARCHAR(20),                        -- northbound / southbound / circular
    origin_region       VARCHAR(255),                       -- e.g. "Hawaii"
    destination_region  VARCHAR(255),                       -- e.g. "Alaska"
    distance_km         INTEGER,
    description         TEXT,
    source              VARCHAR(255),
    created_at          TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 5. REGIONS
-- Named ocean and geographic regions
-- Used for filtering and labelling on the map
-- ============================================================
CREATE TABLE regions (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(255) NOT NULL UNIQUE,       -- e.g. "North Pacific"
    type                VARCHAR(50),                        -- ocean / sea / coastal / polar
    bounding_box        GEOGRAPHY(POLYGON, 4326),           -- PostGIS polygon boundary
    description         TEXT,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 6. SYNC LOG
-- Tracks every data sync job run
-- ============================================================
CREATE TABLE sync_log (
    id                  SERIAL PRIMARY KEY,
    source              VARCHAR(50) NOT NULL,               -- gbif / obis / inaturalist / iucn
    started_at          TIMESTAMP DEFAULT NOW(),
    completed_at        TIMESTAMP,
    records_fetched     INTEGER DEFAULT 0,
    records_inserted    INTEGER DEFAULT 0,
    records_updated     INTEGER DEFAULT 0,
    records_skipped     INTEGER DEFAULT 0,
    status              VARCHAR(20) DEFAULT 'running',      -- running / success / failed
    error_message       TEXT
);
