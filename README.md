# 🐋 whaledata.org

**An interactive 3D globe visualising global whale sightings, migration routes, conservation zones, and shipping lane conflicts.**

Live: [whaledata.org](https://whaledata.org) · API: [api.whaledata.org](https://api.whaledata.org) · Admin: [api.whaledata.org/admin](https://api.whaledata.org/admin)

---

## What it does

whaledata.org aggregates open ocean data from five global sources and renders it as an interactive 3D globe. Users can filter by species, toggle data layers, explore feeding grounds, and visualise where shipping traffic intersects whale habitats.

### Data layers
| Layer | Source | Records |
|-------|--------|---------|
| 🔵 Sightings | GBIF + OBIS | 7,590 |
| 🔴 Strandings | NOAA via OBIS | 12,000 |
| 🟣 Acoustics | NOAA PACM via OBIS | 750 |
| 🟢 iNaturalist | iNaturalist.org | 3,298 |
| 🟡 Historical | GBIF pre-1950 | 1,496 |

**Total: ~25,000 records across 6 species**

### Conservation layers
- **Feeding grounds** — 14 known foraging areas per species with hover details
- **Sonar exercise zones** — 9 naval exercise areas with risk ratings

### Map features
- 3D globe with auto-rotate on load, stops on interaction
- Species filter — fly-to animation takes globe to species habitat on selection
- Cluster mode — dots merge at world zoom, expand as you zoom in
- Animated dashed migration routes with hover detail panel
- 32 global shipping corridors with glow effect and traffic weight
- Year range filter — slide to filter sightings by date
- Share button — encodes current view into a URL
- Near me — flies globe to your location
- Keyboard shortcuts — `1–6` select species, `0` all, `Space` toggle rotation, `Esc` close panels

### Admin panel
Full admin at `api.whaledata.org/admin/` — live DB stats, species editor, sightings manager, manual sync triggers for all 6 data sources, full sync logs.

---

## Species covered

| Species | Sightings | IUCN | Trend |
|---------|-----------|------|-------|
| Humpback whale | 1,213 | LC — Least Concern | Increasing |
| Blue whale | 1,202 | EN — Endangered | Increasing |
| Grey whale | 1,200 | LC — Least Concern | Stable |
| Orca | 1,270 | DD — Data Deficient | Unknown |
| Sperm whale | 688 | VU — Vulnerable | Unknown |
| Fin whale | 2,001 | VU — Vulnerable | Increasing |

---

## Tech stack

### Frontend
- [Vue 3](https://vuejs.org/) — Composition API
- [@maptiler/sdk](https://docs.maptiler.com/sdk-js/) — MapLibre GL JS v5, globe projection
- Syne + DM Mono — typography

### Backend
- [FastAPI](https://fastapi.tiangolo.com/) — REST API, auto docs at `/docs`
- [PostgreSQL](https://www.postgresql.org/) + [PostGIS](https://postgis.net/) — spatial data
- [psycopg2](https://www.psycopg.org/) — database driver

### Data sources
- [GBIF](https://www.gbif.org/) — Global Biodiversity Information Facility
- [OBIS](https://obis.org/) — Ocean Biodiversity Information System
- [NOAA PACM](https://pacm.fisheries.noaa.gov/) — Passive Acoustic Cetacean Map
- [iNaturalist](https://www.inaturalist.org/) — citizen science (research-grade only)

### Infrastructure
- [Coolify](https://coolify.io/) — self-hosted deployment
- Docker — all services containerised
- VPS: Debian, 2 vCPU / 2GB RAM minimum
- Cloudflare — DNS, SSL, redirects

---

## Architecture

```
whaledata/
├── api/                        # FastAPI backend → api.whaledata.org
│   ├── app/
│   │   ├── main.py             # App entry, all routers registered
│   │   ├── database.py         # PostGIS connection (RealDictCursor)
│   │   ├── routers/
│   │   │   ├── species.py
│   │   │   ├── sightings.py
│   │   │   ├── routes.py
│   │   │   ├── strandings.py
│   │   │   ├── acoustics.py
│   │   │   ├── inaturalist.py
│   │   │   ├── historical.py
│   │   │   └── layers.py       # Unified layer summary endpoint
│   │   └── admin/              # Admin panel (HTTP Basic Auth)
│   │       ├── admin.py
│   │       ├── sync_db.py
│   │       ├── sync_gbif.py
│   │       ├── sync_obis.py
│   │       ├── sync_strandings.py
│   │       ├── sync_acoustics.py
│   │       ├── sync_inaturalist.py
│   │       ├── sync_historical.py
│   │       └── templates/
│   ├── schema.sql              # Base schema (6 tables)
│   ├── schema_phase2.sql       # Phase 2 additions (4 tables)
│   └── Dockerfile
│
├── map/                        # Vue 3 frontend → whaledata.org
│   ├── components/
│   │   ├── GlobeMap.vue        # All map layers, interactions, auto-rotate
│   │   ├── Sidebar.vue         # Species filter + detail panel
│   │   ├── LayersPanel.vue     # Data + conservation layer toggles
│   │   ├── ShipLanes.js        # 32 shipping corridor GeoJSON
│   │   └── ConservationLayers.js # Feeding grounds + sonar zones
│   ├── App.vue                 # Root, data fetching, share/nearme/keyboard
│   ├── style.css               # Global dark ocean theme
│   └── Dockerfile
│
├── jobs/                       # Sync workers → Coolify scheduled tasks
│   ├── app/
│   │   ├── sync_gbif.py        # Weekly
│   │   ├── sync_obis.py        # Weekly
│   │   ├── sync_strandings.py  # Monthly
│   │   ├── sync_acoustics.py   # Monthly
│   │   ├── sync_inaturalist.py # Weekly
│   │   └── sync_historical.py  # Yearly
│   └── Dockerfile
│
└── docs/
    ├── DEPLOYMENT.md
    └── API.md
```

---

## API reference

### Core endpoints
```
GET /health
GET /species
GET /sightings/?species=&from_date=&to_date=&limit=5000
GET /sightings/species-summary
GET /routes/
```

### Phase 2 — Data layer endpoints
```
GET /strandings/?species=&limit=2000
GET /strandings/summary
GET /acoustics/?species=&limit=2000
GET /acoustics/summary
GET /inaturalist/?species=&limit=2000
GET /inaturalist/summary
GET /historical/?species=&from_year=&to_year=&limit=2000
GET /historical/summary
GET /layers/summary
```

Full reference: [docs/API.md](docs/API.md) · Interactive: [api.whaledata.org/docs](https://api.whaledata.org/docs)

---

## Sync schedules

| Source | Cron | Frequency |
|--------|------|-----------|
| GBIF | `0 3 * * 0` | Weekly — Sundays 3am |
| OBIS | `0 4 * * 0` | Weekly — Sundays 4am |
| Strandings | `0 3 1 * *` | Monthly |
| Acoustics | `0 4 1 * *` | Monthly |
| iNaturalist | `0 3 * * 3` | Weekly — Wednesdays |
| Historical | `0 5 1 1 *` | Yearly |

---

## Running locally

```bash
git clone https://github.com/Kyraweb/whaledata.git
cd whaledata

# PostGIS
docker run -d --name whaledata-db \
  -e POSTGRES_DB=whaledata \
  -e POSTGRES_USER=whaledata_user \
  -e POSTGRES_PASSWORD=yourpassword \
  -p 5432:5432 postgis/postgis:17-3.5-alpine

# Schema
psql -h localhost -U whaledata_user -d whaledata -f api/schema.sql
psql -h localhost -U whaledata_user -d whaledata -f api/schema_phase2.sql

# API
cd api && pip install -r requirements.txt
cp .env.example .env   # fill in DB_* and ADMIN_* vars
uvicorn app.main:app --reload

# Frontend
cd ../map && npm install
cp .env.example .env   # fill in VITE_API_URL and VITE_MAPTILER_KEY
npm run dev

# Seed data
cd ../jobs && pip install -r requirements.txt
cp .env.example .env
python -m app.sync_gbif
python -m app.sync_obis
python -m app.sync_strandings
python -m app.sync_inaturalist
python -m app.sync_historical
```

For full Coolify self-hosting: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## Environment variables

| Service | Variable | Description |
|---------|----------|-------------|
| API + Jobs | `DB_HOST` | PostGIS hostname |
| API + Jobs | `DB_PORT` | Port (default: `5432`) |
| API + Jobs | `DB_NAME` | Database name |
| API + Jobs | `DB_USER` | Username |
| API + Jobs | `DB_PASSWORD` | Password |
| API | `ADMIN_USER` | Admin panel username |
| API | `ADMIN_PASSWORD` | Admin panel password |
| Map | `VITE_API_URL` | Full API URL (buildtime) |
| Map | `VITE_MAPTILER_KEY` | MapTiler API key (buildtime) |

---

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| `1–6` | Select species (Humpback, Blue, Grey, Sperm, Fin, Orca) |
| `0` | All species |
| `Space` | Toggle globe auto-rotation |
| `Esc` | Close open panels |

---

## Data attribution

- **GBIF** — [gbif.org](https://www.gbif.org) — CC BY 4.0
- **OBIS** — [obis.org](https://obis.org) — CC BY 4.0
- **NOAA PACM** — [pacm.fisheries.noaa.gov](https://pacm.fisheries.noaa.gov) — Public Domain
- **iNaturalist** — [inaturalist.org](https://www.inaturalist.org) — CC BY-NC 4.0
- Species photos — Wikimedia Commons (CC BY / Public Domain)
- Whale audio — NOAA / National Park Service (Public Domain)
- Map tiles — [MapTiler](https://maptiler.com)

---

*Personal hobby project by [Monarch / KyraWeb](https://kyraweb.ca). Built to explore geospatial development with real open ocean data.*
