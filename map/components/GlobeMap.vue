<template>
  <div class="map-wrapper">
    <div ref="mapContainer" class="map-container"></div>

    <!-- Sighting hover popup -->
    <div v-if="hoveredSighting" class="sighting-popup" :style="popupStyle">
      <div class="popup-species">{{ hoveredSighting.species_name }}</div>
      <div class="popup-meta">
        <span>{{ hoveredSighting.source?.toUpperCase() }}</span>
        <span>{{ formatDate(hoveredSighting.sighting_date) }}</span>
      </div>
      <div v-if="hoveredSighting.location_name" class="popup-location">
        {{ hoveredSighting.location_name }}
      </div>
    </div>

    <!-- Route hover panel -->
    <div v-if="hoveredRoute" class="route-panel" :class="{ 'route-panel-mobile': isMobile }">
      <div class="route-name">{{ hoveredRoute.name }}</div>
      <div class="route-meta">
        <span class="route-species-badge">{{ hoveredRoute.species }}</span>
        <span class="route-distance">{{ hoveredRoute.distance_km?.toLocaleString() }} km</span>
      </div>
      <div class="route-desc">{{ hoveredRoute.description }}</div>
    </div>

    <!-- Ship lane hover panel -->
    <div v-if="hoveredLane && shipLanesActive" class="lane-panel" :class="{ 'lane-panel-mobile': isMobile }">
      <div class="lane-name">{{ hoveredLane.name }}</div>
      <div class="lane-traffic" :class="`traffic-${hoveredLane.traffic}`">
        {{ hoveredLane.traffic?.toUpperCase() }} TRAFFIC
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed, nextTick } from 'vue'
import * as maptilersdk from '@maptiler/sdk'
import '@maptiler/sdk/dist/maptiler-sdk.css'
// Ship lanes inlined — avoids Rollup export resolution issues with ShipLanes.js
const shipLanes = [
  { name: 'North Atlantic', traffic: 'high', coordinates: [[-5,48],[-20,45],[-35,42],[-50,42],[-65,42],[-70,42]] },
  { name: 'Suez Canal Corridor', traffic: 'high', coordinates: [[32,30],[33,28],[38,20],[45,15],[50,12],[55,10],[63,8],[70,5],[80,5],[88,8],[95,10],[100,5],[103,2],[105,2]] },
  { name: 'Strait of Malacca', traffic: 'high', coordinates: [[100,5],[103,2],[105,1],[108,2],[114,5]] },
  { name: 'North Pacific West', traffic: 'high', coordinates: [[122,30],[140,35],[155,42],[170,48],[178,52]] },
  { name: 'North Pacific East', traffic: 'high', coordinates: [[-178,52],[-165,55],[-150,52],[-135,48],[-125,42],[-122,37]] },
  { name: 'Panama Canal Pacific', traffic: 'high', coordinates: [[-122,37],[-110,28],[-92,16],[-80,9],[-77,8]] },
  { name: 'Panama Canal Atlantic', traffic: 'high', coordinates: [[-77,8],[-70,15],[-60,25],[-55,30]] },
  { name: 'Cape of Good Hope', traffic: 'medium', coordinates: [[20,-34],[15,-34],[5,-20],[0,-10],[-5,0],[-10,5]] },
  { name: 'Cape Horn', traffic: 'medium', coordinates: [[-70,-55],[-65,-53],[-60,-50],[-55,-45],[-50,-40]] },
  { name: 'South Atlantic', traffic: 'medium', coordinates: [[15,-25],[0,-10],[-20,0],[-35,-5],[-50,-25]] },
  { name: 'Indian Ocean Arabia to Asia', traffic: 'high', coordinates: [[55,20],[65,10],[75,10],[85,10],[95,6],[100,4]] },
  { name: 'Australia East Coast', traffic: 'medium', coordinates: [[147,-43],[152,-32],[153,-27],[150,-17],[145,-15]] },
  { name: 'Australia West Coast', traffic: 'medium', coordinates: [[114,-30],[113,-20],[115,-15],[120,-10]] },
  { name: 'Mediterranean', traffic: 'high', coordinates: [[-5,36],[5,38],[15,38],[25,35],[32,31]] },
  { name: 'North Sea English Channel', traffic: 'high', coordinates: [[-5,48],[0,49],[5,53],[10,56]] },
]

const props = defineProps({
  sightings: { type: Array, default: () => [] },
  routes: { type: Array, default: () => [] },
  selectedSpecies: { type: String, default: null },
  isMobile: { type: Boolean, default: false },
  yearRange: { type: Array, default: () => [1900, 2025] },
  activeLayers: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['map-ready'])

const mapContainer = ref(null)
let map = null
let rotationTimer = null
let animFrame = null
let dashOffset = 0
let layersInited = false

const hoveredSighting = ref(null)
const hoveredRoute = ref(null)
const hoveredLane = ref(null)
const popupStyle = ref({})

// Exposed state for bottom bar buttons
const shipLanesActive = ref(false)
const dateFilterOpen = ref(false)

// Species color palette
const SPECIES_COLORS = {
  'Humpback whale':  '#00e5ff',
  'Blue whale':      '#00b8cc',
  'Grey whale':      '#00c97a',
  'Orca':            '#9664ff',
  'Sperm whale':     '#ffb432',
  'Fin whale':       '#ff6b9d',
}
const DEFAULT_COLOR = '#00e5ff'

function getSpeciesColor(name) {
  for (const [k, v] of Object.entries(SPECIES_COLORS)) {
    if (name?.toLowerCase().includes(k.toLowerCase().split(' ')[0])) return v
  }
  return DEFAULT_COLOR
}

function formatDate(d) {
  if (!d) return ''
  try {
    return new Date(d).toLocaleDateString('en-CA', { year: 'numeric', month: 'short', day: 'numeric' })
  } catch { return d }
}

// ─── Map init ────────────────────────────────────────────────────────────────

onMounted(async () => {
  maptilersdk.config.apiKey = import.meta.env.VITE_MAPTILER_KEY

  map = new maptilersdk.Map({
    container: mapContainer.value,
    style: maptilersdk.MapStyle.DATAVIZ.DARK,
    projection: 'globe',
    center: [0, 20],
    zoom: 1.8,
    minZoom: 1,
    maxZoom: 14,
    attributionControl: false,
    navigationControl: false,
  })

  map.addControl(new maptilersdk.NavigationControl({ showCompass: false }), 'top-right')

  map.on('load', () => {
    initLayers()
    startRotation()
    emit('map-ready')
  })

  map.on('mousedown', () => stopRotation())
  map.on('touchstart', () => stopRotation())
})

onUnmounted(() => {
  stopRotation()
  if (animFrame) cancelAnimationFrame(animFrame)
  map?.remove()
})

// ─── Layer init ───────────────────────────────────────────────────────────────

function initLayers() {
  if (layersInited) return
  layersInited = true

  // ── Sightings ──
  map.addSource('sightings', {
    type: 'geojson',
    data: { type: 'FeatureCollection', features: [] },
  })
  map.addLayer({
    id: 'sightings-hit',
    type: 'circle',
    source: 'sightings',
    paint: {
      'circle-radius': 14,
      'circle-color': 'transparent',
      'circle-opacity': 0,
    },
  })
  map.addLayer({
    id: 'sightings-dots',
    type: 'circle',
    source: 'sightings',
    paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 1, 2.5, 6, 4, 10, 7],
      'circle-color': ['get', 'color'],
      'circle-opacity': 0.85,
    },
  })

  // ── Routes ──
  map.addSource('routes', {
    type: 'geojson',
    data: { type: 'FeatureCollection', features: [] },
  })
  map.addSource('route-endpoints', {
    type: 'geojson',
    data: { type: 'FeatureCollection', features: [] },
  })
  map.addLayer({
    id: 'routes-hit',
    type: 'line',
    source: 'routes',
    paint: { 'line-width': 20, 'line-opacity': 0 },
  })
  map.addLayer({
    id: 'routes-line',
    type: 'line',
    source: 'routes',
    paint: {
      'line-color': ['get', 'color'],
      'line-width': 2.5,
      'line-opacity': 0.8,
      'line-dasharray': [6, 4],
    },
  })
  map.addLayer({
    id: 'route-endpoints-outer',
    type: 'circle',
    source: 'route-endpoints',
    paint: {
      'circle-radius': 7,
      'circle-color': 'transparent',
      'circle-stroke-width': 2,
      'circle-stroke-color': ['get', 'color'],
      'circle-opacity': 0.9,
    },
  })
  map.addLayer({
    id: 'route-endpoints-inner',
    type: 'circle',
    source: 'route-endpoints',
    paint: {
      'circle-radius': 3,
      'circle-color': ['get', 'color'],
      'circle-opacity': 0.9,
    },
  })

  // ── Ship lanes ──
  map.addSource('ship-lanes', {
    type: 'geojson',
    data: buildShipLaneGeoJSON(),
  })
  map.addSource('ship-endpoints', {
    type: 'geojson',
    data: buildShipEndpointsGeoJSON(),
  })
  map.addLayer({
    id: 'ship-lanes-hit',
    type: 'line',
    source: 'ship-lanes',
    layout: { visibility: 'none' },
    paint: { 'line-width': 18, 'line-opacity': 0 },
  })
  map.addLayer({
    id: 'ship-lanes-line',
    type: 'line',
    source: 'ship-lanes',
    layout: { visibility: 'none' },
    paint: {
      'line-color': '#ff9f43',
      'line-width': ['match', ['get', 'traffic'], 'high', 2.5, 'medium', 1.8, 1.2],
      'line-opacity': ['match', ['get', 'traffic'], 'high', 0.9, 'medium', 0.7, 0.5],
      'line-dasharray': [5, 3],
    },
  })
  map.addLayer({
    id: 'ship-endpoints-dots',
    type: 'circle',
    source: 'ship-endpoints',
    layout: { visibility: 'none' },
    paint: {
      'circle-radius': 5,
      'circle-color': 'transparent',
      'circle-stroke-width': 2,
      'circle-stroke-color': '#ff9f43',
      'circle-opacity': 0.85,
    },
  })

  // ── Event handlers ──
  setupHoverHandlers()

  // ── Flush existing data ──
  if (props.sightings.length) updateSightings()
  if (props.routes.length) updateRoutes()

  // ── Animate routes ──
  animateRoutes()
}

// ─── Data update helpers ──────────────────────────────────────────────────────

function buildSightingFeatures() {
  const [minY, maxY] = props.yearRange
  return props.sightings
    .filter(s => {
      // Filter by selected species
      if (props.selectedSpecies && s.species_name !== props.selectedSpecies) return false
      // Filter by year
      if (s.sighting_date) {
        const yr = new Date(s.sighting_date).getFullYear()
        if (yr < minY || yr > maxY) return false
      }
      return true
    })
    .map(s => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [s.longitude, s.latitude] },
      properties: {
        id: s.id,
        species_name: s.species_name,
        source: s.source,
        sighting_date: s.sighting_date,
        location_name: s.location_name,
        color: getSpeciesColor(s.species_name),
      },
    }))
}

function updateSightings() {
  if (!map || !layersInited) return
  const src = map.getSource('sightings')
  if (!src) return
  src.setData({ type: 'FeatureCollection', features: buildSightingFeatures() })
}

function updateRoutes() {
  if (!map || !layersInited) return
  const features = []
  const epFeatures = []
  props.routes.forEach(r => {
    if (!r.coordinates?.length) return
    const color = getSpeciesColor(r.species_name)
    features.push({
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: r.coordinates },
      properties: { id: r.id, name: r.name, species: r.species_name, color, description: r.description, distance_km: r.distance_km },
    })
    const first = r.coordinates[0]
    const last = r.coordinates[r.coordinates.length - 1]
    ;[first, last].forEach(pt => {
      epFeatures.push({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: pt },
        properties: { color },
      })
    })
  })
  map.getSource('routes')?.setData({ type: 'FeatureCollection', features })
  map.getSource('route-endpoints')?.setData({ type: 'FeatureCollection', features: epFeatures })
}

function buildShipLaneGeoJSON() {
  return {
    type: 'FeatureCollection',
    features: shipLanes.map(l => ({
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: l.coordinates },
      properties: { name: l.name, traffic: l.traffic },
    })),
  }
}

function buildShipEndpointsGeoJSON() {
  const features = []
  shipLanes.forEach(l => {
    if (!l.coordinates?.length) return
    ;[l.coordinates[0], l.coordinates[l.coordinates.length - 1]].forEach(pt => {
      features.push({ type: 'Feature', geometry: { type: 'Point', coordinates: pt }, properties: {} })
    })
  })
  return { type: 'FeatureCollection', features }
}

// ─── Watches ──────────────────────────────────────────────────────────────────

watch(() => props.sightings, updateSightings, { deep: false })
watch(() => props.selectedSpecies, updateSightings)
watch(() => props.yearRange, updateSightings, { deep: true })
watch(() => props.routes, updateRoutes, { deep: false })

// ─── Rotation ─────────────────────────────────────────────────────────────────

function startRotation() {
  stopRotation()
  let bearing = map.getBearing()
  function step() {
    bearing = (bearing + 0.08) % 360
    map.setBearing(bearing)
    rotationTimer = requestAnimationFrame(step)
  }
  rotationTimer = requestAnimationFrame(step)
}

function stopRotation() {
  if (rotationTimer) { cancelAnimationFrame(rotationTimer); rotationTimer = null }
}

// ─── Route animation ──────────────────────────────────────────────────────────

function animateRoutes() {
  const dashArrays = [
    [6, 4], [5.8, 4.2], [5.5, 4.5], [5, 5], [4.5, 5.5],
    [4.2, 5.8], [4, 6], [4.2, 5.8], [4.5, 5.5], [5, 5],
    [5.5, 4.5], [5.8, 4.2], [6, 4], [6.2, 3.8],
  ]
  let step = 0
  function tick() {
    if (!map || !layersInited) { animFrame = requestAnimationFrame(tick); return }
    const layer = map.getLayer('routes-line')
    if (layer) map.setPaintProperty('routes-line', 'line-dasharray', dashArrays[step % dashArrays.length])
    step++
    animFrame = requestAnimationFrame(tick)
  }
  // throttle to ~12fps
  let last = 0
  function throttled(ts) {
    if (ts - last > 80) { tick(); last = ts }
    animFrame = requestAnimationFrame(throttled)
  }
  animFrame = requestAnimationFrame(throttled)
}

// ─── Hover handlers ───────────────────────────────────────────────────────────

function setupHoverHandlers() {
  // Sightings
  map.on('mousemove', 'sightings-hit', e => {
    map.getCanvas().style.cursor = 'pointer'
    const f = e.features?.[0]
    if (!f) return
    hoveredSighting.value = f.properties
    const rect = mapContainer.value.getBoundingClientRect()
    popupStyle.value = {
      left: (e.point.x + 14) + 'px',
      top: (e.point.y - 14) + 'px',
    }
  })
  map.on('mouseleave', 'sightings-hit', () => {
    map.getCanvas().style.cursor = ''
    hoveredSighting.value = null
  })

  // Routes
  map.on('mousemove', 'routes-hit', e => {
    map.getCanvas().style.cursor = 'pointer'
    const f = e.features?.[0]
    if (f) hoveredRoute.value = f.properties
  })
  map.on('mouseleave', 'routes-hit', () => {
    map.getCanvas().style.cursor = ''
    hoveredRoute.value = null
  })

  // Ship lanes
  map.on('mousemove', 'ship-lanes-hit', e => {
    if (!shipLanesActive.value) return
    map.getCanvas().style.cursor = 'pointer'
    const f = e.features?.[0]
    if (f) hoveredLane.value = f.properties
    // Dim other lanes
    map.setPaintProperty('ship-lanes-line', 'line-opacity', [
      'case',
      ['==', ['get', 'name'], f?.properties?.name ?? ''], 1,
      0.2,
    ])
  })
  map.on('mouseleave', 'ship-lanes-hit', () => {
    map.getCanvas().style.cursor = ''
    hoveredLane.value = null
    map.setPaintProperty('ship-lanes-line', 'line-opacity', [
      'match', ['get', 'traffic'], 'high', 0.9, 'medium', 0.7, 0.5,
    ])
  })
}

// ─── Exposed methods (called by App.vue bottom bar) ───────────────────────────

function toggleShipLanes() {
  shipLanesActive.value = !shipLanesActive.value
  const vis = shipLanesActive.value ? 'visible' : 'none'
  if (!map || !layersInited) return
  ;['ship-lanes-line', 'ship-lanes-hit', 'ship-endpoints-dots'].forEach(id => {
    if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', vis)
  })
  if (!shipLanesActive.value) hoveredLane.value = null
}

function flyTo(lng, lat, zoom = 5) {
  map?.flyTo({ center: [lng, lat], zoom, duration: 1800 })
  stopRotation()
}

function resetView() {
  map?.flyTo({ center: [0, 20], zoom: 1.8, duration: 1200 })
  startRotation()
}

defineExpose({ toggleShipLanes, shipLanesActive, flyTo, resetView })
</script>

<style scoped>
.map-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

.map-container {
  width: 100%;
  height: 100%;
}

/* ── Sighting popup ── */
.sighting-popup {
  position: absolute;
  background: rgba(5, 8, 16, 0.92);
  border: 1px solid rgba(0, 229, 255, 0.25);
  border-radius: 10px;
  padding: 10px 14px;
  pointer-events: none;
  z-index: 10;
  min-width: 160px;
  backdrop-filter: blur(12px);
}
.popup-species {
  font-family: 'Syne', sans-serif;
  font-size: 13px;
  font-weight: 700;
  color: #e8f4f8;
  margin-bottom: 5px;
}
.popup-meta {
  display: flex;
  gap: 10px;
  font-size: 11px;
  font-family: 'DM Mono', monospace;
  color: #7a9bb5;
  margin-bottom: 3px;
}
.popup-location {
  font-size: 11px;
  color: #3a5a72;
}

/* ── Route panel ── */
.route-panel {
  position: absolute;
  bottom: 72px;
  right: 20px;
  background: rgba(5, 8, 16, 0.92);
  border: 1px solid rgba(0, 229, 255, 0.2);
  border-radius: 12px;
  padding: 14px 18px;
  min-width: 200px;
  max-width: 260px;
  backdrop-filter: blur(12px);
  pointer-events: none;
  z-index: 10;
}
.route-panel-mobile {
  left: 16px;
  right: 16px;
  bottom: 70px;
  max-width: none;
}
.route-name {
  font-family: 'Syne', sans-serif;
  font-size: 13px;
  font-weight: 700;
  color: #e8f4f8;
  margin-bottom: 6px;
}
.route-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.route-species-badge {
  font-size: 10px;
  font-family: 'DM Mono', monospace;
  background: rgba(0, 229, 255, 0.12);
  color: #00e5ff;
  padding: 2px 8px;
  border-radius: 20px;
}
.route-distance {
  font-size: 11px;
  font-family: 'DM Mono', monospace;
  color: #7a9bb5;
}
.route-desc {
  font-size: 12px;
  color: #7a9bb5;
  line-height: 1.5;
}

/* ── Lane panel ── */
.lane-panel {
  position: absolute;
  bottom: 72px;
  right: 20px;
  background: rgba(5, 8, 16, 0.92);
  border: 1px solid rgba(255, 159, 67, 0.3);
  border-radius: 12px;
  padding: 12px 16px;
  backdrop-filter: blur(12px);
  pointer-events: none;
  z-index: 10;
}
.lane-panel-mobile {
  left: 16px;
  right: 16px;
  bottom: 70px;
}
.lane-name {
  font-family: 'Syne', sans-serif;
  font-size: 13px;
  font-weight: 700;
  color: #e8f4f8;
  margin-bottom: 5px;
}
.lane-traffic {
  font-family: 'DM Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.1em;
}
.traffic-high   { color: #ff9f43; }
.traffic-medium { color: rgba(255,159,67,0.7); }
.traffic-low    { color: rgba(255,159,67,0.45); }
</style>
