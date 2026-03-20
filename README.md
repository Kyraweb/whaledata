# 🐋 whaledata.org

**An interactive 3D globe visualising global whale sightings, migration routes, and shipping lane overlaps.**

Live site: [whaledata.org](https://whaledata.org)

---

## What it does

- **4,400+ verified sightings** across 6 species from GBIF and OBIS open data sources
- **Animated migration routes** — arcs curving across the globe showing seasonal journeys
- **Species detail panel** — photo, IUCN conservation status, key facts, and real whale call audio
- **Ship lane overlay** — toggle major global shipping corridors to visualise human/whale conflict zones
- **Mobile responsive** — full globe experience on any device

## Species covered

| Species | Records | IUCN Status |
|---------|---------|-------------|
| Humpback whale | 1,200 | Least Concern |
| Blue whale | 1,200 | Endangered |
| Grey whale | 1,200 | Least Concern |
| Orca | 1,200 | Data Deficient |
| Sperm whale | 687 | Vulnerable |
| Fin whale | 1,986 | Vulnerable |

## Tech stack

**Frontend**
- [Vue 3](https://vuejs.org/) — component framework
- [@maptiler/sdk](https://docs.maptiler.com/sdk-js/) — globe projection + MapLibre GL JS v5
- Syne + DM Mono — typography

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — REST API
- [PostgreSQL](https://www.postgresql.org/) + [PostGIS](https://postgis.net/) — spatial data storage

**Data**
- [GBIF](https://www.gbif.org/) — Global Biodiversity Information Facility
- [OBIS](https://obis.org/) — Ocean Biodiversity Information System

**Infrastructure**
- [Coolify](https://coolify.io/) — self-hosted deployment
- VPS (Debian, 2 vCPU / 2GB RAM)
- Dockerised services

## Architecture

```
whaledata/
├── api/                  # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   └── routers/
│   │       ├── species.py
│   │       ├── sightings.py
│   │       └── routes.py
│   ├── schema.sql
│   └── Dockerfile
│
├── map/                  # Vue 3 frontend
│   ├── components/
│   │   ├── GlobeMap.vue
│   │   ├── Sidebar.vue
│   │   └── ShipLanes.js
│   ├── App.vue
│   ├── style.css
│   └── Dockerfile
│
└── jobs/                 # Data sync workers
    ├── app/
    │   ├── sync_gbif.py
    │   └── sync_obis.py
    └── Dockerfile
```

## API Endpoints

```
GET /health
GET /species
GET /sightings/?limit=5000
GET /sightings/species-summary
GET /routes/
```

## Running locally

**Prerequisites:** Docker, Node 20+, Python 3.11+

```bash
git clone https://github.com/Kyraweb/whaledata.git
cd whaledata

# Start PostGIS
docker run -d --name whaledata-db \
  -e POSTGRES_DB=whaledata \
  -e POSTGRES_USER=whaledata_user \
  -e POSTGRES_PASSWORD=yourpassword \
  -p 5432:5432 postgis/postgis:17-3.5-alpine

# Apply schema
psql -h localhost -U whaledata_user -d whaledata -f api/schema.sql

# Start API
cd api && cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload

# Start frontend
cd ../map && cp .env.example .env
npm install && npm run dev

# Sync data
cd ../jobs && cp .env.example .env
python -m app.sync_gbif
python -m app.sync_obis
```

## Data attribution

- **GBIF** — [gbif.org](https://www.gbif.org) — CC BY 4.0
- **OBIS** — [obis.org](https://obis.org) — CC BY 4.0
- Species photos — Wikimedia Commons (CC BY / Public Domain)
- Whale call audio — NOAA / National Park Service (Public Domain)

## About

Personal hobby project by [Monarch](https://kyraweb.ca). Built to explore full-stack geospatial development with real open ocean data.

---

*Data updated daily via scheduled sync.*
