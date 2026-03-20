# whaledata.org — API Reference

Base URL: `https://api.whaledata.org`

All endpoints return JSON. No authentication required for public endpoints.

---

## Endpoints

### Health Check

```
GET /health
```

Returns service status.

**Response**
```json
{
  "status": "ok",
  "service": "whaledata-api"
}
```

---

### List Species

```
GET /species
```

Returns all species in the database with conservation metadata.

**Response**
```json
{
  "data": [
    {
      "id": 1,
      "scientific_name": "Megaptera novaeangliae",
      "common_name": "Humpback whale",
      "conservation_status": "LC",
      "population_trend": "increasing"
    }
  ]
}
```

---

### Get Species by ID

```
GET /species/{id}
```

Returns a single species record.

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Species ID |

**Example**
```bash
curl https://api.whaledata.org/species/1
```

---

### List Sightings

```
GET /sightings/
```

Returns whale sighting records with coordinates. Designed to feed directly into map visualisations.

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `species` | string | — | Filter by common name, e.g. `Humpback whale` |
| `from_date` | string | — | Start date, format `YYYY-MM-DD` |
| `to_date` | string | — | End date, format `YYYY-MM-DD` |
| `limit` | integer | `5000` | Max records to return (max: `10000`) |

**Example**
```bash
# All sightings (up to 5000)
curl https://api.whaledata.org/sightings/

# Blue whale sightings only
curl "https://api.whaledata.org/sightings/?species=Blue+whale"

# Sightings from 2020 onwards
curl "https://api.whaledata.org/sightings/?from_date=2020-01-01"

# Combined filters
curl "https://api.whaledata.org/sightings/?species=Humpback+whale&from_date=2022-01-01&limit=100"
```

**Response**
```json
{
  "data": [
    {
      "id": 1234,
      "common_name": "Humpback whale",
      "scientific_name": "Megaptera novaeangliae",
      "longitude": -157.823,
      "latitude": 21.304,
      "sighted_on": "2024-03-15",
      "region": "Hawaii",
      "source": "gbif",
      "source_url": "https://www.gbif.org/occurrence/4567890",
      "individual_count": 1
    }
  ],
  "count": 1200,
  "filters": {
    "species": "Humpback whale",
    "from_date": null,
    "to_date": null
  }
}
```

---

### Species Sighting Summary

```
GET /sightings/species-summary
```

Returns a count of sightings per species with date ranges. Used to populate species filter UI.

**Example**
```bash
curl https://api.whaledata.org/sightings/species-summary
```

**Response**
```json
{
  "data": [
    {
      "common_name": "Humpback whale",
      "scientific_name": "Megaptera novaeangliae",
      "sighting_count": 1203,
      "earliest": "2023-01-01",
      "latest": "2026-02-28"
    },
    {
      "common_name": "Blue whale",
      "scientific_name": "Balaenoptera musculus",
      "sighting_count": 1202,
      "earliest": "2024-01-10",
      "latest": "2026-03-11"
    }
  ]
}
```

---

### Migration Routes

```
GET /routes/
```

Returns all whale migration routes as GeoJSON LineStrings. Used to render animated migration arcs on the globe.

**Example**
```bash
curl https://api.whaledata.org/routes/
```

**Response**
```json
{
  "data": [
    {
      "id": 1,
      "name": "North Pacific — Hawaii to Alaska",
      "common_name": "Humpback whale",
      "scientific_name": "Megaptera novaeangliae",
      "season": "summer",
      "direction": "northbound",
      "origin_region": "Hawaii",
      "destination_region": "Gulf of Alaska",
      "distance_km": 5000,
      "description": "Humpbacks winter in warm Hawaiian waters to breed and calve, then migrate north to rich Alaskan feeding grounds each summer.",
      "geojson": {
        "type": "LineString",
        "coordinates": [
          [-158, 21],
          [-155, 25],
          [-152, 30],
          [-148, 38],
          [-143, 46],
          [-140, 52],
          [-148, 57],
          [-152, 58.5]
        ]
      }
    }
  ],
  "count": 7
}
```

---

## Species Reference

| Common Name | Scientific Name | IUCN | GBIF Records |
|-------------|----------------|------|-------------|
| Humpback whale | *Megaptera novaeangliae* | LC | 1,200 |
| Blue whale | *Balaenoptera musculus* | EN | 1,200 |
| Grey whale | *Eschrichtius robustus* | LC | 1,200 |
| Orca | *Orcinus orca* | DD | 1,200 |
| Sperm whale | *Physeter macrocephalus* | VU | 687 |
| Fin whale | *Balaenoptera physalus* | VU | 1,986 (OBIS) |

---

## Data Sources

Sighting data is sourced from:

- **GBIF** (Global Biodiversity Information Facility) — [gbif.org](https://gbif.org)
  - Taxon keys used: Humpback (2440898), Blue (2440718), Orca (2440483), Grey (2440714), Sperm (2440764), Fin (2440706)
  - Filtered with `hasCoordinate=true` and `hasGeospatialIssue=false`

- **OBIS** (Ocean Biodiversity Information System) — [obis.org](https://obis.org)
  - Used for Fin whale data supplementation
  - AphiaID: 137092

Data is updated daily via scheduled sync.

---

## Usage Examples

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

### Filter by species and date range

```javascript
const params = new URLSearchParams({
  species:   'Blue whale',
  from_date: '2020-01-01',
  limit:     '1000'
})
const res  = await fetch(`https://api.whaledata.org/sightings/?${params}`)
const data = await res.json()
```

### Load migration routes

```javascript
const res    = await fetch('https://api.whaledata.org/routes/')
const data   = await res.json()
const routes = data.data

// Each route has a .geojson property ready to use as a GeoJSON geometry
routes.forEach(route => {
  console.log(route.name, route.geojson.coordinates.length, 'waypoints')
})
```

### Get species summary for a filter UI

```javascript
const res     = await fetch('https://api.whaledata.org/sightings/species-summary')
const data    = await res.json()
const species = data.data

species.forEach(s => {
  console.log(`${s.common_name}: ${s.sighting_count} sightings`)
})
```

---

## Rate Limits

There are currently no enforced rate limits. Please be considerate — avoid hammering the API with high-frequency requests. For bulk data access, consider downloading from [GBIF](https://gbif.org) or [OBIS](https://obis.org) directly.

---

## CORS

The API allows cross-origin requests from any origin for public endpoints. If you are self-hosting and restricting access, update `allow_origins` in `api/app/main.py`.

---

## Self-Hosting

See [DEPLOYMENT.md](./DEPLOYMENT.md) for instructions on running your own instance.

---

## Attribution

If you use this API in a project, please credit:

- **whaledata.org** — [whaledata.org](https://whaledata.org)
- **GBIF** — [gbif.org](https://gbif.org)
- **OBIS** — [obis.org](https://obis.org)
