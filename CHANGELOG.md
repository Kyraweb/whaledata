# Changelog — whaledata.org

All notable changes to this project, documented across multiple development sprints.
Built iteratively over several weeks with AI-assisted development using [Claude](https://claude.ai) by Anthropic.

---

## [2.0.0] — Sprint 3 — March 2026

### Added
- **Phase 2 data layers** — 4 new data sources beyond GBIF/OBIS sightings
  - Strandings layer (NOAA/OBIS) — ~12,000 stranding events
  - Acoustics layer (NOAA PACM/OBIS) — ~750 hydrophone detections
  - iNaturalist layer — ~3,300 research-grade citizen science observations
  - Historical layer (GBIF pre-1950) — ~1,500 digitised whaling records
- **Floating layers panel** — toggle each data layer independently, per-species counts
- **Conservation layers** — feeding ground polygons and naval sonar exercise zones
- **Phase 3 conservation angle** — shipping lane overlap with whale habitats
- **Share button** — encodes full view state (species, layers, year range) into a URL
- **Near me button** — geolocation, flies globe to user's coordinates
- **Keyboard shortcuts** — `1–6` select species, `0` all, `Space` toggle rotation, `Esc` close panels
- **URL state restore** — shared links restore full view state on load
- **Year range filter** — dual-thumb slider to explore data from 1785 to present
- **Help/how-to modal** — full platform documentation accessible from globe
- **Weekly email alerts** — subscribe to new sightings digest via AWS SES
  - Double opt-in confirmation
  - Per-species, per-region, per-layer filter preferences
  - One-click unsubscribe
- **Admin panel rebuilt** — moved inside API service, no separate container
  - Dashboard with live DB stats
  - Species editor (IUCN status, population trend)
  - Sightings manager (browse, filter, delete)
  - Sync logs with duration and error messages
  - Manual sync for all 6 data sources
  - Subscribers page with CSV export
- **Open Graph meta tags** — rich social sharing cards for Twitter/X, LinkedIn, Facebook
- **API error state** — banner with retry button when API is unreachable
- **Mobile improvements** — sticky sheet header, scrollable content, layer toggles in hamburger sheet
- **32 global shipping corridors** — expanded from 15, with orange glow effect
- **Cluster mode** — all 5 data layers cluster at world zoom, expand on click
- **Auto-rotate globe** on load — stops on user interaction
- **Fly-to animation** — globe rotates smoothly to selected species habitat
- **Consolidated schema** — `schema_phase2.sql` adds 4 new tables

### Fixed
- `fix: async def for edit_species, RedirectResponse import at top level`
- `fix: separate sync_database.py without RealDictCursor, surface DB errors on dashboard`
- `fix: sync_log column is completed_at not finished_at`
- `fix: handle NULL finished_at in sync_log duration calculation`
- `fix: remove invalid basisOfRecord param from GBIF API call`
- `fix: ship lane routes crossing land — Korea/Canada, Australia east coast, Australia east-west`
- `fix: ocean filter for layer data, clustering for all phase 2 layers`
- `fix: mobile lp-btn-row positioning, add Acoustics and Conservation section to mobile sheet`
- `fix: mobile sheet max-height with dvh, sticky header always visible, scrollable content`
- `fix: year slider position, ship lanes glow effect, expanded shipping routes`
- `fix: bottom-btn base CSS lost when share/near me moved to top-right`
- `fix: allow sightings layer to be toggled off, hide all dots when all layers off`
- `fix: restore bottom-btn base CSS lost when share/near me moved to top-right`
- `fix: iNaturalist SQL ON CONFLICT clause, strandings type cast, historical year format`
- `fix: acoustics PACM → OBIS (PACM API blocked by hosting network)`
- `fix: handle partial date formats in strandings sync (year-only, year-month, date ranges)`
- `fix: reject single/double digit non-date values in strandings parse_date`
- `fix: correct iNaturalist taxon IDs for Blue whale, Fin whale and Orca`
- `fix: add parse_date to historical sync — handle year-only and year-month date formats`
- `fix: sync_log column is completed_at not finished_at`
- `fix: add watch to Vue imports in App.vue`
- `fix: mobile action buttons, layer toggles in sheet, desktop button overlap`
- `fix: add data attribution footer to mobile sheet`
- `fix: update attribution to all data sources on desktop and mobile`
- `fix: help grid single column on mobile`

### Changed
- Admin panel moved from standalone Coolify service into the API service at `/admin/`
- All sync scripts now run from jobs service scheduled tasks (6 cron jobs)
- Year slider replaced with popup button to clean up bottom bar layout
- Share and Near Me moved to top-right corner
- Data Layers and Conservation split into separate floating panels

---

## [1.5.0] — Sprint 2 — March 2026

### Added
- `feat: animated migration route lines with hover detail panel`
- `feat: species detail panel with photo, IUCN status, facts and whale call audio`
- `feat: ship lanes overlay with toggle button` — 15 major shipping corridors
- `feat: ship lane endpoint dots, hover highlight and info panel`
- `feat: OBIS sync script for Fin whale data`
- `feat: mobile responsive layout with bottom sheet sidebar`
- `feat: species info button and detail sheet on mobile`
- `feat: admin dashboard with auth, sync logs, species view, manual sync trigger`
- `feat: upgrade maplibre to v5, enable globe projection`
- `feat: switch to @maptiler/sdk for native globe projection support`
- `feat: globe projection with atmosphere and dark ocean style`
- `feat: local whale images and sounds assets`
- `docs: README with tech stack, architecture, setup instructions`
- DEPLOYMENT.md and API.md documentation

### Fixed
- `fix: route endpoint dots + wider hover hit areas for sightings`
- `fix: reduce sighting hit area to avoid stealing nearby dot hovers`
- `fix: wrap setFog in try-catch to prevent crashing layer init`
- `fix: set globe projection after map load instead of in constructor`
- `fix: revert to dataviz-dark, try globe via styledata event`
- `fix: remove setFog which crashes MapLibre v5 and blocks layer init`
- `fix: fetch style JSON and inject globe projection to avoid style.load loop`
- `fix: declare build args in Dockerfile, remove invalid fog from style object`
- `fix: populate sources immediately after init to fix race condition with API data`
- `fix: guard layer init against duplicate style.load calls`
- `fix: ocean style, remove duplicate controls, visible dots, filter land coords`
- `fix: switch back to dark style for route and dot visibility`
- `fix: correct Orca GBIF taxon key (2440522 → 2440483)`
- `fix: tighten land filter to avoid blocking Arabian Sea and Indian Ocean sightings`
- `fix: add Paraguay/Bolivia inland filter, keep Ecuador/Colombia Pacific coast`
- `fix: accurate ship lane coordinates for major global trade routes`
- `fix: split Pacific routes at antimeridian to fix globe rendering spike`
- `fix: sidebar hidden by default on mobile, slides up as sheet on tap`
- `fix: hamburger menu, correct z-index, backdrop behind sheet`
- `fix: self-contained mobile sheet in App.vue, desktop Sidebar unchanged`
- `fix: sidebar footer always visible when species panel open`
- `fix: robust error handling in admin to prevent 500 on DB errors`
- `fix: exclude GBIF records with geospatial issues`
- `fix: robust date parsing for OBIS date formats`
- `fix: use Wikimedia Special:FilePath URLs to bypass ORB blocking`
- `fix: audio file extension ogg not mp3`
- `fix: use config scientific names instead of GBIF record names`
- `fix: remove wipe on startup — rely on upsert to skip duplicates`

---

## [1.0.0] — Sprint 1 — March 2026

### Added
- `feat: FastAPI skeleton with health check and species endpoints`
- `feat: add sightings API endpoints with filtering`
- `feat: migration routes seed script and API endpoint`
- `feat: GBIF sync job for 6 key whale species`
- `feat: Vue map app with globe, sighting markers, and species sidebar`
- Initial PostgreSQL + PostGIS schema — species, sightings, migration_routes, sync_log tables
- Coolify deployment configuration for API, map, and jobs services
- Docker containers for all three services
- CORS configuration for API
- Environment variable configuration

### Fixed
- `fix: correct monorepo folder structure`
- `fix: correct monorepo structure and add schema`
- `fix: smooth zoom and correct popup positioning`
- `fix: switch to GPU-rendered circle layers for performance and correct popups`
- `fix: use config scientific names instead of GBIF record names`
- `fix: remove wipe on startup — rely on upsert to skip duplicates`

---

## Data Sources

| Source | First added | Records (approx) |
|--------|------------|-----------------|
| GBIF sightings | Sprint 1 | 5,590 |
| OBIS Fin whale | Sprint 2 | 2,000 |
| NOAA Strandings | Sprint 3 | 12,000 |
| iNaturalist | Sprint 3 | 3,300 |
| Acoustics (NOAA PACM/OBIS) | Sprint 3 | 750 |
| Historical whaling (GBIF pre-1950) | Sprint 3 | 1,500 |

**Total: ~25,000+ records**

---

## Built With

Developed with assistance from [Claude](https://claude.ai) by [Anthropic](https://anthropic.com) — used for architecture decisions, code generation, debugging, and documentation throughout the entire build.
