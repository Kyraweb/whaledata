# Changelog — whaledata.org

All notable changes to this project documented across every iteration.
Built over approximately 12 months from initial concept to production platform.

Built with assistance from [Claude](https://claude.ai) by [Anthropic](https://anthropic.com).

---

## [2.5.0] — 2026-03 — Contact, API Monitoring & Documentation

### Added
- `feat: contact/feedback form — sends to alerts@whaledata.org via AWS SES`
- `feat: API usage logging middleware — tracks every request with IP, path, response time`
- `feat: API usage admin tab — daily counts, top endpoints, top IPs, flagged threshold`
- `feat: Google Analytics GA4 integration`
- `feat: CHANGELOG.md — full iterative build history`
- `feat: schema_full.sql — consolidated single-file schema replacing schema.sql + schema_phase2.sql`
- `feat: docs/DATABASE.md — database setup guide, table reference, useful queries`
- `feat: Claude/Anthropic credit in README`

### Fixed
- `fix: contact form endpoint URL /contact → /alerts/contact`

### Changed
- `docs: remove admin panel URL from public README`

---

## [2.4.0] — 2026-02 — Open Graph, Error States & OG Image

### Added
- `feat: Open Graph and Twitter Card meta tags in index.html`
- `feat: og-image.jpg — layered SVG/Illustrator source for social sharing card`
- `feat: og:image:alt and fb:app_id meta tags`
- `feat: API error banner with retry button when API is unreachable`
- `feat: mobile attribution footer in hamburger sheet`

### Fixed
- `fix: update attribution text to include OBIS, iNaturalist, NOAA on desktop and mobile`
- `fix: help grid single column on mobile`

---

## [2.3.0] — 2026-02 — Help Modal & Weekly Email Alerts

### Added
- `feat: help/how-to modal with full platform documentation`
- `feat: keyboard shortcuts reference in help modal`
- `feat: data layers explained section in help modal`
- `feat: conservation layers explained in help modal`
- `feat: weekly email alerts via AWS SES — subscribe, confirm, unsubscribe`
- `feat: double opt-in confirmation email with branded HTML template`
- `feat: per-species, per-region, per-layer alert filter preferences`
- `feat: weekly digest job — sends HTML email with new records since last run`
- `feat: subscribers admin page — view, export CSV, delete`
- `feat: Cloudflare Email Routing for alerts@whaledata.org → personal inbox`

### Fixed
- `fix: AWS SES credential signature mismatch — Is Literal flag on secret key`
- `fix: restore bottom-btn base CSS lost when share/near me moved to top-right`

---

## [2.2.0] — 2026-01 — Conservation Layers & Phase 4 UI

### Added
- `feat: ConservationLayers.js — feeding ground polygons for all 6 species`
- `feat: naval sonar exercise zones layer (9 known zones with risk rating)`
- `feat: feeding grounds hover popup — shows species and location name`
- `feat: sonar zones hover popup — shows authority and risk level`
- `feat: share button — encodes species, year range, active layers into URL`
- `feat: URL state restore — shared links restore full view state on load`
- `feat: near me button — geolocation, flies globe to user coordinates`
- `feat: keyboard shortcuts — 1-6 species, 0 all, Space rotation, Esc close`
- `feat: split layers panel into Data Layers and Conservation separate buttons`
- `feat: year filter as bottom-right button opening popup panel`
- `feat: year-filtered dot on button when range is active`

### Fixed
- `fix: bottom bar layout — share/near me right-anchored, ship lanes clear of overlap`
- `fix: mobile — hide layer buttons, all controls in hamburger sheet`
- `fix: mobile sheet max-height with dvh, sticky header always visible`
- `fix: mobile sheet scrollable content with min-height:0 on flex children`
- `fix: conservation layer visibility toggle watcher`
- `fix: lp-btn-row display:none on mobile (controls live in sheet)`

---

## [2.1.0] — 2025-12 — Layers Panel & Map UX

### Added
- `feat: LayersPanel.vue — floating panel with per-layer toggle switches`
- `feat: layer count badges on toggle buttons`
- `feat: per-species record count shown when species is selected`
- `feat: all on / all off buttons in layers panel`
- `feat: auto-rotate globe on load — stops on any user interaction`
- `feat: fly-to animation — globe rotates to species habitat on selection`
- `feat: cluster mode — dots group at world zoom, expand on click`
- `feat: year range dual-thumb slider — filters all sightings layers`
- `feat: sightings layer toggle — can now be turned off completely`

### Fixed
- `fix: watch import missing from Vue imports in App.vue`
- `fix: allow sightings layer to be toggled off, hide clusters and dots`
- `fix: ocean filter applied to all layer data before rendering`
- `fix: cluster click zoom for all phase 2 layers`
- `fix: layer visibility toggle includes cluster and cluster-count layers`

---

## [2.0.0] — 2025-11 — Phase 2 Data Layers

### Added
- `feat: schema_phase2.sql — 4 new tables: strandings, acoustics, inaturalist_sightings, historical_sightings`
- `feat: sync_strandings.py — NOAA stranding events via OBIS`
- `feat: sync_acoustics.py — NOAA PACM acoustic detections via OBIS`
- `feat: sync_inaturalist.py — research-grade iNaturalist observations`
- `feat: sync_historical.py — pre-1950 GBIF whaling records`
- `feat: routers/strandings.py — GET /strandings/ and /strandings/summary`
- `feat: routers/acoustics.py — GET /acoustics/ and /acoustics/summary`
- `feat: routers/inaturalist.py — GET /inaturalist/ and /inaturalist/summary`
- `feat: routers/historical.py — GET /historical/ and /historical/summary`
- `feat: routers/layers.py — GET /layers/summary unified count endpoint`
- `feat: debug mode for all sync scripts (--debug, --limit=N flags)`
- `feat: OBIS fallback in acoustics sync when PACM API unreachable`

### Fixed
- `fix: iNaturalist SQL ON CONFLICT clause — string literal not valid`
- `fix: strandings individual_count cast from float string to int`
- `fix: historical year format — GBIF needs 1500,1950 not ,1950`
- `fix: parse_date handles year-only, year-month, date ranges from OBIS`
- `fix: reject single/double digit non-date values in strandings`
- `fix: correct iNaturalist taxon IDs — Blue whale 41467, Fin 41468, Orca 41446`
- `fix: parse_date added to historical sync for sighted_on field`
- `fix: acoustics rewrote to use OBIS directly (PACM blocked by hosting network)`

---

## [1.9.0] — 2025-10 — Admin Panel Rebuilt Inside API

### Added
- `feat: admin panel moved into API service at /admin/ — no separate container`
- `feat: Jinja2 templates for admin UI`
- `feat: species editor — edit IUCN status and population trend via modal`
- `feat: sightings manager — browse, filter by species/source/region, delete records`
- `feat: sync logs page with duration calculation`
- `feat: manual sync page — trigger all 6 jobs from browser with live output`
- `feat: sync_database.py — plain cursor DB for sync scripts (no RealDictCursor)`

### Fixed
- `fix: async def for edit_species, RedirectResponse import at top level`
- `fix: sync_log column is completed_at not finished_at`
- `fix: handle NULL finished_at in sync_log duration calculation`
- `fix: surface actual DB error on dashboard instead of silently returning 0s`
- `fix: truncate error message in sync logs, fix date column wrapping`
- `fix: add requests to admin requirements for sync scripts`
- `fix: remove invalid basisOfRecord param from GBIF API call (400 error)`

---

## [1.8.0] — 2025-09 — Ship Lanes Expansion & Mobile Polish

### Added
- `feat: expanded shipping lanes from 15 to 32 global corridors`
- `feat: ship lane glow effect — orange blur layer behind routes`
- `feat: Northern Sea Route, Gulf of Guinea, East Africa, Black Sea, Caribbean lanes`
- `feat: Australia East-West, South Pacific, trans-Indian Ocean corridors`

### Fixed
- `fix: ship lane routes crossing land — Korea/Canada arc through open Pacific`
- `fix: Australia East Coast to Asia — follows Torres Strait correctly`
- `fix: Australia East to West — routes south around Tasmania`
- `fix: year slider position — moved to bottom-right, no longer overlaps ship lanes`
- `fix: mobile responsive bottom buttons — ship lanes icon-only on mobile`

---

## [1.7.0] — 2025-08 — Mobile Responsive Layout

### Added
- `feat: mobile responsive layout with bottom sheet sidebar`
- `feat: hamburger button top-left on mobile`
- `feat: stats bar pinned to bottom on mobile`
- `feat: species info button and detail sheet on mobile`
- `feat: backdrop closes sheet on tap`
- `feat: mobile-specific CSS overrides for map controls`

### Fixed
- `fix: sidebar hidden by default on mobile, slides up as sheet on tap`
- `fix: hamburger menu correct z-index, backdrop behind sheet`
- `fix: self-contained mobile sheet in App.vue, desktop Sidebar unchanged`
- `fix: sidebar footer always visible when species panel open`
- `fix: sheet transition cubic-bezier for native feel`

---

## [1.6.0] — 2025-07 — Species Detail Panel & Audio

### Added
- `feat: species detail panel — photo, IUCN badge, facts, description`
- `feat: whale call audio player per species (.ogg format)`
- `feat: IUCN badge colour coding (LC green, EN orange, VU yellow, DD grey)`
- `feat: local whale photos and audio assets in map/public/assets/`
- `feat: species collapse back to all-species view`

### Fixed
- `fix: audio file extension ogg not mp3`
- `fix: use Wikimedia Special:FilePath URLs to bypass ORB CORS blocking`
- `fix: switch photo URLs to fix broken Wikimedia hotlinking`
- `fix: correct audio MIME type to ogg`

---

## [1.5.0] — 2025-06 — Ship Lanes Overlay

### Added
- `feat: ShipLanes.js — 15 major shipping corridor GeoJSON`
- `feat: ship lanes overlay with toggle button (bottom centre)`
- `feat: ship lane endpoint dots at start and end of each corridor`
- `feat: ship lane hover highlight — dims other lanes, shows info panel`
- `feat: ship lane info panel — name and traffic level`
- `feat: ship lanes hidden by default, orange colour scheme`

### Fixed
- `fix: add missing toggleShipLanes function`
- `fix: accurate ship lane coordinates for major global trade routes`
- `fix: split Pacific routes at antimeridian to fix globe rendering spike`

---

## [1.4.0] — 2025-05 — OBIS Fin Whale Sync

### Added
- `feat: sync_obis.py — OBIS Fin whale data (AphiaID 137092)`
- Fin whale records from Ocean Biodiversity Information System
- OBIS sync scheduled task (weekly)

### Fixed
- `fix: robust date parsing for OBIS ISO date formats`
- `fix: tighten land filter to avoid blocking Arabian Sea sightings`
- `fix: add Paraguay/Bolivia inland filter, keep Ecuador/Colombia Pacific coast`
- `fix: correct Orca GBIF taxon key 2440522 → 2440483`
- `fix: exclude GBIF records with hasGeospatialIssue=true`

---

## [1.3.0] — 2025-04 — Migration Routes

### Added
- `feat: migration_routes table in schema`
- `feat: seed_migration_routes.py — 7 routes across 5 species`
- `feat: routers/routes.py — GET /routes/ endpoint returning GeoJSON`
- `feat: animated dashed route lines on globe with species colours`
- `feat: route hover detail panel — name, season, direction, distance, description`
- `feat: route endpoint ringed dots at origin and destination`
- `feat: wide invisible hit areas for easy hover on thin lines`

### Fixed
- `fix: route endpoint dots + wider hover hit areas for sightings`
- `fix: reduce sighting hit area to avoid stealing nearby dot hovers`

---

## [1.2.0] — 2025-03 — Globe Projection

### Added
- `feat: upgrade @maptiler/sdk replacing maplibre-gl`
- `feat: globe projection with dark ocean style`
- `feat: GPU-rendered circle layers replacing DOM markers`
- `feat: sighting dot glow layer for visual depth`
- `feat: sighting hover popup with species, date, region, source`
- `feat: species colour coding per layer`

### Fixed
- `fix: switch to @maptiler/sdk for native globe projection support`
- `fix: fetch style JSON and inject globe projection to avoid style.load loop`
- `fix: declare build args in Dockerfile so Vite sees env vars at build time`
- `fix: remove setFog which crashes MapLibre v5 and blocks layer init`
- `fix: populate sources immediately after init to fix race condition`
- `fix: guard layer init against duplicate style.load calls`
- `fix: switch back to dataviz-dark style for dot visibility`

---

## [1.1.0] — 2025-02 — Vue Frontend & Species Sidebar

### Added
- `feat: Vue 3 + Vite map frontend`
- `feat: MapLibre GL map with sighting dot markers`
- `feat: species sidebar — filter by species, show count`
- `feat: App.vue data fetching from FastAPI`
- `feat: land coordinate filter — removes inland false positives`
- `feat: Dockerfile for map service`
- `feat: VITE_API_URL and VITE_MAPTILER_KEY environment variable setup`
- `feat: Coolify deployment for map service`

### Fixed
- `fix: smooth zoom and correct popup positioning`
- `fix: switch to GPU-rendered circle layers for performance`
- `fix: correct monorepo folder structure`

---

## [1.0.2] — 2025-01 — GBIF Data Sync

### Added
- `feat: sync_gbif.py — syncs up to 1200 sightings per species from GBIF`
- 6 species: Humpback, Blue, Grey, Orca, Sperm, Fin whale
- `ON CONFLICT DO NOTHING` deduplication
- Coolify scheduled task (daily cron)
- `feat: jobs/ service Dockerfile`

### Fixed
- `fix: remove wipe on startup — rely on upsert to skip duplicates`
- `fix: use config scientific names instead of GBIF record names`
- `fix: GBIF restart storm — jobs container ran as one-shot not daemon`

---

## [1.0.1] — 2024-12 — FastAPI Backend

### Added
- `feat: FastAPI skeleton with health check endpoint`
- `feat: GET /species and GET /species/{id} endpoints`
- `feat: GET /sightings/ with species, date, limit filtering`
- `feat: PostgreSQL + PostGIS schema — species, sightings, sync_log tables`
- `feat: RealDictCursor database connection`
- `feat: CORS configuration for Vue frontend`
- `feat: Dockerfile for API service`
- `feat: Coolify deployment for API service`
- `feat: .env.example configuration template`

---

## [1.0.0] — 2024-11 — Project Initialisation

### Added
- `feat: monorepo structure — api/, map/, jobs/, docs/`
- `feat: PostgreSQL + PostGIS database on Coolify`
- `feat: initial schema.sql`
- `feat: .gitignore for Python, Node, environment files`
- `feat: README.md`
- `feat: GitHub repository setup`
- `feat: Coolify server setup on Debian VPS`
- `feat: domain DNS configuration via Cloudflare`

---

## Data Milestones

| Date | Event |
|------|-------|
| 2024-11 | Project started |
| 2024-12 | First API endpoint live |
| 2025-01 | First 4,288 whale sightings loaded from GBIF |
| 2025-03 | Globe projection achieved after multiple iterations |
| 2025-04 | Migration routes animated on globe |
| 2025-06 | Ship lanes overlay added |
| 2025-07 | Mobile responsive layout |
| 2025-09 | 7,590 sightings with OBIS Fin whale data |
| 2025-11 | Phase 2 launch — 4 new data sources, 25,000+ total records |
| 2025-12 | Layers panel, conservation zones, year filter |
| 2026-01 | Share button, near me, keyboard shortcuts |
| 2026-02 | Email alerts via AWS SES |
| 2026-03 | Contact form, API monitoring, full documentation |

---

*Built with [Claude](https://claude.ai) by [Anthropic](https://anthropic.com)*
