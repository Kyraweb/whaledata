# whaledata.org — API Reference

Base URL: `https://api.whaledata.org`

All endpoints return JSON. No authentication required. Interactive docs: [api.whaledata.org/docs](https://api.whaledata.org/docs)

---

## Core endpoints

### Health check
```
GET /health
```
```json
{ "status": "ok", "service": "whaledata-api", "version": "2.0.0" }
```

---

### Species
```
GET /species
```
Returns all species with conservation metadata.

```json
{
  "data": [{
    "id": 1,
    "scientific_name": "Megaptera novaeangliae",
    "common_name": "Humpback whale",
    "conservation_status": "LC",
    "population_trend": "increasing"
  }]
}
```

```
GET /species/{id}
```
Returns a single species by ID.

---

### Sightings
```
GET /sightings/
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `species` | string | Filter by common name e.g. `Humpback whale` |
| `from_date` | string | Start date `YYYY-MM-DD` |
| `to_date` | string | End date `YYYY-MM-DD` |
| `limit` | integer | Max records (default: 5000, max: 10000) |

```bash
# All sightings
curl "https://api.whaledata.org/sightings/?limit=5000"

# Species + date filter
curl "https://api.whaledata.org/sightings/?species=Blue+whale&from_date=2020-01-01"
```

```json
{
  "data": [{
    "id": 1234,
    "common_name": "Humpback whale",
    "scientific_name": "Megaptera novaeangliae",
    "longitude": -157.823,
    "latitude": 21.304,
    "sighted_on": "2024-03-15",
    "region": "Hawaii",
    "source": "gbif",
    "source_url": "https://www.gbif.org/occurrence/4567890"
  }],
  "count": 1200
}
```

```
GET /sightings/species-summary
```
Returns count per species with date ranges. Used to populate the species filter UI.

---

### Migration routes
```
GET /routes/
```
Returns migration routes as GeoJSON LineStrings. Each route has waypoint coordinates ready to render on a map.

```json
{
  "data": [{
    "id": 1,
    "name": "North Pacific — Hawaii to Alaska",
    "common_name": "Humpback whale",
    "season": "summer",
    "direction": "northbound",
    "origin_region": "Hawaii",
    "destination_region": "Gulf of Alaska",
    "distance_km": 5000,
    "geojson": {
      "type": "LineString",
      "coordinates": [[-158, 21], [-155, 25], [-148, 57]]
    }
  }]
}
```

---

## Phase 2 — Data layer endpoints

All layer endpoints share the same pattern: filtered list + summary.

### Strandings
```
GET /strandings/
```
Whale stranding events (beached or dead on shore). Source: NOAA via OBIS.

| Parameter | Type | Description |
|-----------|------|-------------|
| `species` | string | Filter by common name |
| `from_date` | string | Start date `YYYY-MM-DD` |
| `to_date` | string | End date `YYYY-MM-DD` |
| `condition` | string | `alive` / `dead` / `unknown` |
| `limit` | integer | Max records (default: 2000) |

```json
{
  "data": [{
    "id": 1,
    "common_name": "Humpback whale",
    "longitude": -70.123,
    "latitude": 42.456,
    "stranded_on": "2023-04-12",
    "condition": "dead",
    "region": "Cape Cod",
    "country": "United States",
    "source": "obis"
  }],
  "layer": "strandings"
}
```

```
GET /strandings/summary
```
Count per species with date ranges.

---

### Acoustics
```
GET /acoustics/
```
Underwater acoustic detections from hydrophones. Source: NOAA PACM via OBIS.

| Parameter | Type | Description |
|-----------|------|-------------|
| `species` | string | Filter by common name |
| `from_date` | string | Start date |
| `to_date` | string | End date |
| `call_type` | string | `song` / `contact` / `click` / `unknown` |
| `limit` | integer | Max records (default: 2000) |

```json
{
  "data": [{
    "id": 1,
    "common_name": "Humpback whale",
    "longitude": -158.5,
    "latitude": 22.1,
    "detected_on": "2022-11-03",
    "call_type": "song",
    "confidence": "high",
    "platform": "HARP buoy Hawaii"
  }],
  "layer": "acoustics"
}
```

```
GET /acoustics/summary
```

---

### iNaturalist
```
GET /inaturalist/
```
Community-verified research-grade whale observations. Source: iNaturalist.org.

| Parameter | Type | Description |
|-----------|------|-------------|
| `species` | string | Filter by common name |
| `from_date` | string | Start date |
| `to_date` | string | End date |
| `quality_grade` | string | `research` / `needs_id` / `casual` |
| `limit` | integer | Max records (default: 2000) |

```json
{
  "data": [{
    "id": 1,
    "common_name": "Grey whale",
    "longitude": -124.3,
    "latitude": 48.5,
    "observed_on": "2024-02-14",
    "quality_grade": "research",
    "region": "Olympic Peninsula",
    "source_url": "https://www.inaturalist.org/observations/12345",
    "observer": "ocean_watcher"
  }],
  "layer": "inaturalist"
}
```

```
GET /inaturalist/summary
```

---

### Historical
```
GET /historical/
```
Pre-1950 records from digitised whaling logs and historical surveys. Source: GBIF.

| Parameter | Type | Description |
|-----------|------|-------------|
| `species` | string | Filter by common name |
| `from_year` | integer | Start year e.g. `1800` |
| `to_year` | integer | End year e.g. `1950` |
| `limit` | integer | Max records (default: 2000) |

```json
{
  "data": [{
    "id": 1,
    "common_name": "Sperm whale",
    "longitude": -30.5,
    "latitude": 15.2,
    "sighted_on": "1847-01-01",
    "year": 1847,
    "vessel": "Ship log — Pacific voyage",
    "region": "North Atlantic"
  }],
  "layer": "historical"
}
```

```
GET /historical/summary
```
Returns count per species with earliest and latest year.

---

### Layers summary
```
GET /layers/summary
```
Returns counts for **all layers in one request**. Used by the frontend to populate the layers panel without 4 separate API calls.

```json
{
  "layers": {
    "sightings":   { "total": 7590,  "data": [{ "common_name": "...", "source": "gbif", "count": 1213 }] },
    "strandings":  { "total": 12000, "data": [{ "common_name": "...", "count": 2000 }] },
    "acoustics":   { "total": 750,   "data": [{ "common_name": "...", "count": 662 }] },
    "inaturalist": { "total": 3298,  "data": [{ "common_name": "...", "count": 1200 }] },
    "historical":  { "total": 1496,  "data": [{ "common_name": "...", "count": 1200 }] }
  }
}
```

---

## Usage examples

### Fetch all sightings for a map
```javascript
const res  = await fetch('https://api.whaledata.org/sightings/?limit=5000')
const data = await res.json()

const geojson = {
  type: 'FeatureCollection',
  features: data.data.map(s => ({
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [s.longitude, s.latitude] },
    properties: { species: s.common_name, date: s.sighted_on }
  }))
}
```

### Load all layer counts
```javascript
const res    = await fetch('https://api.whaledata.org/layers/summary')
const data   = await res.json()
const layers = data.layers

console.log(`Sightings: ${layers.sightings.total}`)
console.log(`Strandings: ${layers.strandings.total}`)
```

### Filter by species across layers
```javascript
const species = 'Humpback whale'
const [sightings, strandings, inat] = await Promise.all([
  fetch(`https://api.whaledata.org/sightings/?species=${encodeURIComponent(species)}&limit=2000`).then(r => r.json()),
  fetch(`https://api.whaledata.org/strandings/?species=${encodeURIComponent(species)}&limit=2000`).then(r => r.json()),
  fetch(`https://api.whaledata.org/inaturalist/?species=${encodeURIComponent(species)}&limit=2000`).then(r => r.json()),
])
```

---

## Species reference

| Common Name | Scientific Name | IUCN | GBIF Taxon Key |
|-------------|----------------|------|----------------|
| Humpback whale | *Megaptera novaeangliae* | LC | 2440898 |
| Blue whale | *Balaenoptera musculus* | EN | 2440718 |
| Grey whale | *Eschrichtius robustus* | LC | 2440714 |
| Orca | *Orcinus orca* | DD | 2440483 |
| Sperm whale | *Physeter macrocephalus* | VU | 2440764 |
| Fin whale | *Balaenoptera physalus* | VU | 2440706 |

---

## Rate limits

No enforced rate limits. For bulk data access download directly from [GBIF](https://gbif.org) or [OBIS](https://obis.org).

## CORS

Public endpoints allow all origins. If self-hosting with restricted CORS, update `allow_origins` in `api/app/main.py`.

## Self-hosting

See [DEPLOYMENT.md](./DEPLOYMENT.md).

## Attribution

If using this API please credit: **whaledata.org**, **GBIF**, **OBIS**, **NOAA**, **iNaturalist**.
