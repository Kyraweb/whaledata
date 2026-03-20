<template>
  <div ref="mapContainer" class="globe-map" />

  <!-- Ship lanes button -->
  <button class="ship-lanes-btn" :class="{ active: shipLanesVisible }" @click="toggleShipLanes">
    <span class="ship-lanes-icon">🚢</span>
    <span class="ship-lanes-label">{{ shipLanesVisible ? 'Hide ship lanes' : 'Show ship lanes' }}</span>
  </button>

  <!-- Route hover panel -->
  <Transition name="panel">
    <div v-if="hoveredShipLane" class="route-panel ship-lane-panel">
      <div class="route-panel-species" style="color: #ff9f43">🚢 Shipping Lane</div>
      <div class="route-panel-name">{{ hoveredShipLane.name }}</div>
      <div class="route-panel-meta">
        <span class="route-tag" style="border-color:rgba(255,159,67,0.3);background:rgba(255,159,67,0.08);color:#ff9f43">
          {{ hoveredShipLane.traffic }} traffic
        </span>
      </div>
    </div>
  </Transition>

  <Transition name="panel">
    <div v-if="hoveredRoute" class="route-panel">
      <div class="route-panel-species" :style="{ color: getSpeciesColor(hoveredRoute.common_name) }">
        {{ hoveredRoute.common_name }}
      </div>
      <div class="route-panel-name">{{ hoveredRoute.name }}</div>
      <div class="route-panel-meta">
        <span class="route-tag">{{ hoveredRoute.season }}</span>
        <span class="route-tag">{{ hoveredRoute.direction }}</span>
        <span class="route-tag">{{ Number(hoveredRoute.distance_km).toLocaleString() }} km</span>
      </div>
      <div class="route-panel-path">
        <span class="route-origin">{{ hoveredRoute.origin_region }}</span>
        <span class="route-arrow">→</span>
        <span class="route-dest">{{ hoveredRoute.destination_region }}</span>
      </div>
      <div class="route-panel-desc">{{ hoveredRoute.description }}</div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as maptilersdk from '@maptiler/sdk'
import { SHIP_LANES_GEOJSON } from './ShipLanes.js'
import '@maptiler/sdk/dist/maptiler-sdk.css'

const props = defineProps({
  sightings:       { type: Array,  default: () => [] },
  migrationRoutes: { type: Array,  default: () => [] },
  selectedSpecies: { type: String, default: '' },
  yearRange:       { type: Array,  default: () => [1900, 2030] },
})

const emit = defineEmits(['user-interacted'])

const mapContainer     = ref(null)
const hoveredRoute     = ref(null)
const hoveredShipLane  = ref(null)
const shipLanesVisible = ref(false)

let map            = null
let popup          = null
let animationFrame = null
let rotateFrame    = null
let layersReady    = false
let userInteracted = false

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY || ''

const SPECIES_COLORS = {
  'Humpback whale': '#00e5ff',
  'Blue whale':     '#4d9fff',
  'Grey whale':     '#a8c5da',
  'Sperm whale':    '#7eb8d4',
  'Fin whale':      '#5dd4b8',
  'Orca':           '#ff6b9d',
}

// Habitat centers for fly-to on species selection
const SPECIES_CENTERS = {
  'Humpback whale': { center: [-40, 10],  zoom: 2.2 },
  'Blue whale':     { center: [-120, 35], zoom: 2.2 },
  'Grey whale':     { center: [-140, 50], zoom: 2.2 },
  'Sperm whale':    { center: [-40, 15],  zoom: 2.0 },
  'Fin whale':      { center: [-30, 52],  zoom: 2.2 },
  'Orca':           { center: [-130, 50], zoom: 2.2 },
}

function getSpeciesColor(name) { return SPECIES_COLORS[name] || '#ffffff' }

function sightingsGeoJSON(sightings, yearRange) {
  const [minYear, maxYear] = yearRange || [1900, 2030]
  return {
    type: 'FeatureCollection',
    features: (sightings || [])
      .filter(s => {
        if (s.longitude == null || s.latitude == null) return false
        if (s.sighted_on) {
          const y = parseInt(s.sighted_on.substring(0, 4))
          if (!isNaN(y) && (y < minYear || y > maxYear)) return false
        }
        return true
      })
      .map(s => ({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [parseFloat(s.longitude), parseFloat(s.latitude)] },
        properties: {
          common_name:     s.common_name || '',
          scientific_name: s.scientific_name || '',
          region:          s.region || '',
          sighted_on:      s.sighted_on || '',
          source:          s.source || '',
          color:           getSpeciesColor(s.common_name)
        }
      }))
  }
}

function routesGeoJSON(routes) {
  return {
    type: 'FeatureCollection',
    features: (routes || []).filter(r => r.geojson?.coordinates?.length).map(r => ({
      type: 'Feature', geometry: r.geojson,
      properties: {
        id: r.id, name: r.name, common_name: r.common_name, scientific_name: r.scientific_name,
        season: r.season, direction: r.direction, origin_region: r.origin_region,
        destination_region: r.destination_region, distance_km: r.distance_km,
        description: r.description, color: getSpeciesColor(r.common_name)
      }
    }))
  }
}

function routeEndpointsGeoJSON(routes) {
  const features = []
  ;(routes || []).filter(r => r.geojson?.coordinates?.length >= 2).forEach(r => {
    const coords = r.geojson.coordinates
    const color  = getSpeciesColor(r.common_name)
    features.push({ type: 'Feature', geometry: { type: 'Point', coordinates: coords[0] }, properties: { color } })
    features.push({ type: 'Feature', geometry: { type: 'Point', coordinates: coords[coords.length - 1] }, properties: { color } })
  })
  return { type: 'FeatureCollection', features }
}

// ── Auto-rotate ───────────────────────────────────────────────

function startRotate() {
  if (userInteracted) return
  rotateFrame = requestAnimationFrame(function rotate() {
    if (userInteracted || !map) return
    const center = map.getCenter()
    map.setCenter([center.lng + 0.06, center.lat])
    rotateFrame = requestAnimationFrame(rotate)
  })
}

function stopRotate() {
  if (rotateFrame) { cancelAnimationFrame(rotateFrame); rotateFrame = null }
}

function onUserInteract() {
  if (!userInteracted) {
    userInteracted = true
    stopRotate()
    emit('user-interacted')
  }
}

// ── Layers ────────────────────────────────────────────────────

function initLayers() {
  // Clustered sightings source
  map.addSource('sightings', {
    type: 'geojson',
    data: sightingsGeoJSON(props.sightings, props.yearRange),
    cluster: true,
    clusterMaxZoom: 4,
    clusterRadius: 40,
  })

  map.addSource('routes',          { type: 'geojson', data: routesGeoJSON(props.migrationRoutes) })
  map.addSource('route-endpoints', { type: 'geojson', data: routeEndpointsGeoJSON(props.migrationRoutes) })

  // ── Route layers ──────────────────────────────────────────
  map.addLayer({ id: 'routes-glow', type: 'line', source: 'routes',
    layout: { 'line-cap': 'round', 'line-join': 'round' },
    paint: { 'line-color': ['get', 'color'], 'line-width': 14, 'line-opacity': 0.4, 'line-blur': 4 }
  })
  map.addLayer({ id: 'routes-base', type: 'line', source: 'routes',
    layout: { 'line-cap': 'round', 'line-join': 'round' },
    paint: { 'line-color': ['get', 'color'], 'line-width': 3, 'line-opacity': 1 }
  })
  map.addLayer({ id: 'routes-dash', type: 'line', source: 'routes',
    layout: { 'line-cap': 'butt', 'line-join': 'round' },
    paint: { 'line-color': ['get', 'color'], 'line-width': 4, 'line-opacity': 1, 'line-dasharray': [0, 4, 3] }
  })
  map.addLayer({ id: 'routes-hitarea', type: 'line', source: 'routes',
    layout: { 'line-cap': 'round', 'line-join': 'round' },
    paint: { 'line-color': ['get', 'color'], 'line-width': 20, 'line-opacity': 0 }
  })
  map.addLayer({ id: 'route-endpoints-ring', type: 'circle', source: 'route-endpoints',
    paint: { 'circle-radius': 7, 'circle-color': 'transparent',
             'circle-stroke-width': 1.5, 'circle-stroke-color': ['get', 'color'], 'circle-stroke-opacity': 0.7 }
  })
  map.addLayer({ id: 'route-endpoints-dot', type: 'circle', source: 'route-endpoints',
    paint: { 'circle-radius': 3.5, 'circle-color': ['get', 'color'], 'circle-opacity': 0.9 }
  })

  // ── Cluster layers ────────────────────────────────────────
  // Cluster bubble
  map.addLayer({ id: 'clusters', type: 'circle', source: 'sightings',
    filter: ['has', 'point_count'],
    paint: {
      'circle-color': ['step', ['get', 'point_count'], '#00b8cc', 50, '#00e5ff', 200, '#4d9fff'],
      'circle-radius': ['step', ['get', 'point_count'], 18, 50, 24, 200, 32],
      'circle-opacity': 0.85,
    }
  })
  // Cluster count label
  map.addLayer({ id: 'cluster-count', type: 'symbol', source: 'sightings',
    filter: ['has', 'point_count'],
    layout: {
      'text-field': '{point_count_abbreviated}',
      'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
      'text-size': 12,
    },
    paint: { 'text-color': '#050810' }
  })
  // Individual dots (only shown when not clustered)
  map.addLayer({ id: 'sightings-glow', type: 'circle', source: 'sightings',
    filter: ['!', ['has', 'point_count']],
    paint: { 'circle-radius': 10, 'circle-color': ['get', 'color'], 'circle-opacity': 0.1, 'circle-blur': 1 }
  })
  map.addLayer({ id: 'sightings-dot', type: 'circle', source: 'sightings',
    filter: ['!', ['has', 'point_count']],
    paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 1, 4, 5, 6, 10, 9],
      'circle-color': ['get', 'color'], 'circle-opacity': 1,
    }
  })
  map.addLayer({ id: 'sightings-hitarea', type: 'circle', source: 'sightings',
    filter: ['!', ['has', 'point_count']],
    paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 1, 6, 5, 8, 10, 11],
             'circle-color': 'transparent', 'circle-opacity': 0 }
  })

  // Cluster click → zoom in
  map.on('click', 'clusters', (e) => {
    const features = map.queryRenderedFeatures(e.point, { layers: ['clusters'] })
    const clusterId = features[0].properties.cluster_id
    map.getSource('sightings').getClusterExpansionZoom(clusterId, (err, zoom) => {
      if (err) return
      map.easeTo({ center: features[0].geometry.coordinates, zoom })
    })
  })
  map.on('mouseenter', 'clusters', () => { map.getCanvas().style.cursor = 'pointer' })
  map.on('mouseleave', 'clusters', () => { map.getCanvas().style.cursor = '' })

  // ── Interactions ──────────────────────────────────────────
  map.on('mouseenter', 'routes-hitarea', (e) => {
    map.getCanvas().style.cursor = 'pointer'
    const p = e.features[0].properties
    hoveredRoute.value = p
    map.setPaintProperty('routes-base', 'line-opacity', ['case', ['==', ['get', 'id'], p.id], 1, 0.3])
    map.setPaintProperty('routes-dash', 'line-width',   ['case', ['==', ['get', 'id'], p.id], 3, 2])
  })
  map.on('mouseleave', 'routes-hitarea', () => {
    map.getCanvas().style.cursor = ''
    hoveredRoute.value = null
    map.setPaintProperty('routes-base', 'line-opacity', 1)
    map.setPaintProperty('routes-dash', 'line-width', 4)
  })
  map.on('mouseenter', 'sightings-hitarea', (e) => {
    map.getCanvas().style.cursor = 'pointer'
    const feature = e.features[0]
    const coords  = feature.geometry.coordinates.slice()
    const p       = feature.properties
    const color   = p.color || '#00e5ff'
    if (popup) popup.remove()
    popup = new maptilersdk.Popup({ closeButton: false, closeOnClick: false, offset: 12, maxWidth: '240px' })
      .setLngLat(coords)
      .setHTML(`
        <div style="font-family:'Syne',sans-serif;padding:2px 0">
          <div style="font-size:13px;font-weight:600;color:${color};margin-bottom:4px">${p.common_name}</div>
          <div style="font-size:11px;color:#7a9bb5;font-style:italic;margin-bottom:8px">${p.scientific_name}</div>
          <div style="font-size:11px;color:#7a9bb5;line-height:2">
            ${p.region ? '📍 ' + p.region + '<br/>' : ''}
            ${p.sighted_on ? '📅 ' + p.sighted_on + '<br/>' : ''}
            ${p.source ? '🔬 ' + p.source.toUpperCase() : ''}
          </div>
        </div>
      `).addTo(map)
  })
  map.on('mouseleave', 'sightings-hitarea', () => {
    map.getCanvas().style.cursor = ''
    if (popup) { popup.remove(); popup = null }
  })

  // ── Ship lanes ────────────────────────────────────────────
  const shipEndpoints = {
    type: 'FeatureCollection',
    features: SHIP_LANES_GEOJSON.features.flatMap(f => {
      const coords = f.geometry.coordinates
      return [
        { type: 'Feature', geometry: { type: 'Point', coordinates: coords[0] }, properties: {} },
        { type: 'Feature', geometry: { type: 'Point', coordinates: coords[coords.length - 1] }, properties: {} }
      ]
    })
  }
  map.addSource('ship-lanes', { type: 'geojson', data: SHIP_LANES_GEOJSON })
  map.addSource('ship-endpoints', { type: 'geojson', data: shipEndpoints })
  map.addLayer({ id: 'ship-lanes-glow', type: 'line', source: 'ship-lanes',
    layout: { 'line-cap': 'round', 'line-join': 'round', visibility: 'none' },
    paint: {
      'line-color': '#ff9f43',
      'line-width': ['match', ['get', 'traffic'], 'high', 12, 'medium', 8, 5],
      'line-opacity': 0.12,
      'line-blur': 6,
    }
  })

  map.addLayer({ id: 'ship-lanes-line', type: 'line', source: 'ship-lanes',
    layout: { 'line-cap': 'round', 'line-join': 'round', visibility: 'none' },
    paint: { 'line-color': '#ff9f43', 'line-width': ['match', ['get', 'traffic'], 'high', 2, 'medium', 1.5, 1],
             'line-opacity': ['match', ['get', 'traffic'], 'high', 0.7, 'medium', 0.5, 0.35], 'line-dasharray': [3, 2] }
  })
  map.addLayer({ id: 'ship-endpoints-ring', type: 'circle', source: 'ship-endpoints',
    layout: { visibility: 'none' },
    paint: { 'circle-radius': 5, 'circle-color': 'transparent', 'circle-stroke-width': 1.5, 'circle-stroke-color': '#ff9f43', 'circle-stroke-opacity': 0.7 }
  })
  map.addLayer({ id: 'ship-endpoints-dot', type: 'circle', source: 'ship-endpoints',
    layout: { visibility: 'none' },
    paint: { 'circle-radius': 2.5, 'circle-color': '#ff9f43', 'circle-opacity': 0.9 }
  })
  map.addLayer({ id: 'ship-lanes-hitarea', type: 'line', source: 'ship-lanes',
    layout: { 'line-cap': 'round', visibility: 'none' },
    paint: { 'line-color': '#ff9f43', 'line-width': 20, 'line-opacity': 0 }
  })
  map.on('mouseenter', 'ship-lanes-hitarea', (e) => {
    map.getCanvas().style.cursor = 'pointer'
    const p = e.features[0].properties
    hoveredShipLane.value = p
    map.setPaintProperty('ship-lanes-line', 'line-opacity', ['case', ['==', ['get', 'name'], p.name], 1, 0.3])
    map.setPaintProperty('ship-lanes-line', 'line-width',   ['case', ['==', ['get', 'name'], p.name], 4, ['match', ['get', 'traffic'], 'high', 2, 'medium', 1.5, 1]])
  })
  map.on('mouseleave', 'ship-lanes-hitarea', () => {
    map.getCanvas().style.cursor = ''
    hoveredShipLane.value = null
    map.setPaintProperty('ship-lanes-line', 'line-opacity', ['match', ['get', 'traffic'], 'high', 0.7, 'medium', 0.5, 0.35])
    map.setPaintProperty('ship-lanes-line', 'line-width', ['match', ['get', 'traffic'], 'high', 2, 'medium', 1.5, 1])
  })

  layersReady = true
  animateDash()

  // Start auto-rotate after layers are ready
  setTimeout(startRotate, 800)
}

// ── Dash animation ────────────────────────────────────────────

const DASH_FRAMES = [
  [0,4,3],[0.5,4,2.5],[1,4,2],[1.5,4,1.5],[2,4,1],[2.5,4,0.5],[3,4,0],
  [0,0.5,3,3.5],[0,1,3,3],[0,1.5,3,2.5],[0,2,3,2],[0,2.5,3,1.5],[0,3,3,1],[0,3.5,3,0.5]
]
let dashStep = 0
function animateDash() {
  if (!map || !map.getLayer('routes-dash')) return
  map.setPaintProperty('routes-dash', 'line-dasharray', DASH_FRAMES[dashStep])
  dashStep = (dashStep + 1) % DASH_FRAMES.length
  animationFrame = setTimeout(animateDash, 80)
}

function toggleShipLanes() {
  if (!map || !map.getLayer('ship-lanes-line')) return
  shipLanesVisible.value = !shipLanesVisible.value
  const v = shipLanesVisible.value ? 'visible' : 'none'
  map.setLayoutProperty('ship-lanes-glow',     'visibility', v)
  map.setLayoutProperty('ship-lanes-line',     'visibility', v)
  map.setLayoutProperty('ship-lanes-hitarea',  'visibility', v)
  map.setLayoutProperty('ship-endpoints-ring', 'visibility', v)
  map.setLayoutProperty('ship-endpoints-dot',  'visibility', v)
  if (!shipLanesVisible.value) hoveredShipLane.value = null
}

// ── Lifecycle ─────────────────────────────────────────────────

onMounted(() => {
  maptilersdk.config.apiKey = MAPTILER_KEY

  map = new maptilersdk.Map({
    container:        mapContainer.value,
    style:            maptilersdk.MapStyle.DATAVIZ.DARK,
    center:           [0, 20],
    zoom:             1.8,
    projection:       'globe',
    attributionControl: false,
  })

  // Stop rotation on any user interaction
  map.on('mousedown',  onUserInteract)
  map.on('touchstart', onUserInteract)
  map.on('wheel',      onUserInteract)
  map.on('dragstart',  onUserInteract)

  map.on('load', () => { initLayers() })
})

onUnmounted(() => {
  stopRotate()
  if (animationFrame) clearTimeout(animationFrame)
  if (popup) popup.remove()
  if (map) map.remove()
})

// Update sightings when data or year range changes
watch([() => props.sightings, () => props.yearRange], ([sightings, yearRange]) => {
  if (layersReady && map?.getSource('sightings'))
    map.getSource('sightings').setData(sightingsGeoJSON(sightings, yearRange))
}, { deep: true })

watch(() => props.migrationRoutes, (val) => {
  if (layersReady && map?.getSource('routes')) {
    map.getSource('routes').setData(routesGeoJSON(val))
    map.getSource('route-endpoints').setData(routeEndpointsGeoJSON(val))
  }
}, { deep: true })

// Fly-to on species selection
watch(() => props.selectedSpecies, (species) => {
  if (!map || !species) return
  const target = SPECIES_CENTERS[species]
  if (!target) return
  userInteracted = true  // stop rotation when species selected
  stopRotate()
  map.flyTo({
    center:   target.center,
    zoom:     target.zoom,
    duration: 2000,
    essential: true,
  })
})
</script>

<style scoped>
.globe-map { width: 100%; height: 100%; }

.route-panel {
  position: fixed; bottom: 32px; right: 32px; width: 300px;
  background: rgba(8, 13, 26, 0.95); backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 229, 255, 0.2); border-radius: 14px;
  padding: 20px; z-index: 200; box-shadow: 0 0 40px rgba(0, 229, 255, 0.08);
}
.route-panel-species { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 6px; }
.route-panel-name { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 10px; line-height: 1.4; }
.route-panel-meta { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
.route-tag { font-size: 10px; padding: 2px 8px; border-radius: 20px; background: rgba(0,229,255,0.08); border: 1px solid rgba(0,229,255,0.15); color: var(--text-secondary); text-transform: capitalize; font-family: var(--font-mono); }
.route-panel-path { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; font-size: 11px; }
.route-origin, .route-dest { color: var(--text-primary); font-weight: 500; }
.route-arrow { color: var(--cyan); flex-shrink: 0; }
.route-panel-desc { font-size: 11px; color: var(--text-secondary); line-height: 1.7; }
.panel-enter-active, .panel-leave-active { transition: all 0.2s ease; }
.panel-enter-from, .panel-leave-to { opacity: 0; transform: translateY(8px); }

.ship-lanes-btn {
  position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 8px; padding: 10px 20px;
  background: rgba(8, 13, 26, 0.9); backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 159, 67, 0.3); border-radius: 30px;
  color: rgba(255, 159, 67, 0.7); font-family: var(--font-display);
  font-size: 13px; font-weight: 500; cursor: pointer; z-index: 200;
  transition: all 0.2s ease; white-space: nowrap;
}
.ship-lanes-btn:hover { background: rgba(255, 159, 67, 0.12); border-color: rgba(255, 159, 67, 0.6); color: rgba(255, 159, 67, 1); }
.ship-lanes-btn.active { background: rgba(255, 159, 67, 0.15); border-color: rgba(255, 159, 67, 0.8); color: #ff9f43; box-shadow: 0 0 20px rgba(255, 159, 67, 0.2); }
.ship-lanes-icon { font-size: 15px; }

@media (max-width: 767px) {
  .ship-lanes-btn { bottom: 76px; font-size: 12px; padding: 8px 16px; }
  .route-panel { bottom: 76px; right: 12px; left: 12px; width: auto; }
}
</style>
