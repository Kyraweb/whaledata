# 🐋 whaledata.org

A personal hobby project visualising whale populations, sightings, and migration routes across the globe — powered by open data sources.

> Personal project. Not affiliated with any organisation. Data is sourced from open public APIs.

**Live site:** [whaledata.org](https://whaledata.org)

---

## Structure

| Folder | Description |
|--------|-------------|
| `api/` | FastAPI backend — serves whale data to the frontend |
| `map/` | Vue.js frontend — 3D globe with migration animations |
| `jobs/` | Data sync workers — pulls from GBIF, iNaturalist, and other open APIs |

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Frontend | Vue.js + MapLibre GL JS + Deck.gl |
| Backend | FastAPI (Python) |
| Database | PostgreSQL + PostGIS |
| Map Tiles | Maptiler |
| Hosting | VPS + Coolify |

---

## Getting Started

Each subfolder has its own README with setup instructions:

- [API setup](./api/README.md)
- [Map setup](./map/README.md)
- [Jobs setup](./jobs/README.md)

---

## Data Sources

- [GBIF](https://www.gbif.org/) — Global Biodiversity Information Facility
- [OBIS](https://obis.org/) — Ocean Biodiversity Information System
- [iNaturalist](https://www.inaturalist.org/) — Community sightings
- [IUCN Red List](https://www.iucnredlist.org/) — Conservation status

---

## License

MIT — free to use, fork, and learn from.
