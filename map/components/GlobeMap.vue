<template>
  <div ref="mapContainer" class="globe-map" />

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
import '@maptiler/sdk/dist/maptiler-sdk.css'

const props = defineProps({
  sightings:       { type: Array,  default: () => [] },
  migrationRoutes: { type: Array,  default: () => [] },
  selectedSpecies: { type: String, default: '' }
})

const mapContainer = ref(null)
const hoveredRoute = ref(null)
let map            = null
let popup          = null
let animationFrame = null
let layersReady    = false

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY || ''

const SPECIES_COLORS = {
  'Humpback whale': '#00e5ff',
  'Blue whale':     '#4d9fff',
  'Grey whale':     '#a8c5da',
  'Sperm whale':    '#7eb8d4',
  'Fin whale':      '#5dd4b8',
  'Orca':           '#ff6b9d',
}

function getSpeciesColor(name) {
  return SPECIES_COLORS[name] || '#ffffff'
}

function sightingsGeoJSON(sightings) {
  return {
    type: 'FeatureCollection',
    features: (sightings || [])
      .filter(s => {
        if (s.longitude == null || s.latitude == null) return false
        const lng = parseFloat(s.longitude)
        const lat = parseFloat(s.latitude)
        // Filter out inland South America cluster (Amazon basin - clearly not ocean)
        if (lng > -75 && lng < -35 && lat > -25 && lat < 10) return false
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
          color: getSpeciesColor(s.common_name)
        }
      }))
  }
}

function routesGeoJSON(routes) {
  return {
    type: 'FeatureCollection',
    features: (routes || [])
      .filter(r => r.geojson?.coordinates?.length)
      .map(r => ({
        type: 'Feature',
        geometry: r.geojson,
        properties: {
          id: r.id, name: r.name,
          common_name: r.common_name, scientific_name: r.scientific_name,
          season: r.season, direction: r.direction,
          origin_region: r.origin_region, destination_region: r.destination_region,
          distance_km: r.distance_km, description: r.description,
          color: getSpeciesColor(r.common_name)
        }
      }))
  }
}

function routeEndpointsGeoJSON(routes) {
  const features = []
  ;(routes || [])
    .filter(r => r.geojson?.coordinates?.length >= 2)
    .forEach(r => {
      const coords = r.geojson.coordinates
      const color  = getSpeciesColor(r.common_name)
      features.push({ type: 'Feature', geometry: { type: 'Point', coordinates: coords[0] }, properties: { color } })
      features.push({ type: 'Feature', geometry: { type: 'Point', coordinates: coords[coords.length - 1] }, properties: { color } })
    })
  return { type: 'FeatureCollection', features }
}

function initLayers() {
  map.addSource('routes',          { type: 'geojson', data: routesGeoJSON(props.migrationRoutes) })
  map.addSource('route-endpoints', { type: 'geojson', data: routeEndpointsGeoJSON(props.migrationRoutes) })
  map.addSource('sightings',       { type: 'geojson', data: sightingsGeoJSON(props.sightings) })

  map.addLayer({ id: 'routes-glow', type: 'line', source: 'routes',
    layout: { 'line-cap': 'round', 'line-join': 'round' },
    paint: { 'line-color': ['get', 'color'], 'line-width': 10, 'line-opacity': 0.15, 'line-blur': 6 }
  })
  map.addLayer({ id: 'routes-base', type: 'line', source: 'routes',
    layout: { 'line-cap': 'round', 'line-join': 'round' },
    paint: { 'line-color': ['get', 'color'], 'line-width': 2.5, 'line-opacity': 0.7 }
  })
  map.addLayer({ id: 'routes-dash', type: 'line', source: 'routes',
    layout: { 'line-cap': 'butt', 'line-join': 'round' },
    paint: { 'line-color': ['get', 'color'], 'line-width': 3, 'line-opacity': 1, 'line-dasharray': [0, 4, 3] }
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
  map.addLayer({ id: 'sightings-glow', type: 'circle', source: 'sightings',
    paint: { 'circle-radius': 10, 'circle-color': ['get', 'color'], 'circle-opacity': 0.1, 'circle-blur': 1 }
  })
  map.addLayer({ id: 'sightings-dot', type: 'circle', source: 'sightings',
    paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 1, 4, 5, 6, 10, 9],
      'circle-color': ['get', 'color'], 'circle-opacity': 1,
      'circle-stroke-width': 2, 'circle-stroke-color': '#0a1628', 'circle-stroke-opacity': 0.8
    }
  })
  map.addLayer({ id: 'sightings-hitarea', type: 'circle', source: 'sightings',
    paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 1, 6, 5, 8, 10, 11],
             'circle-color': 'transparent', 'circle-opacity': 0 }
  })

  map.on('mouseenter', 'routes-hitarea', (e) => {
    map.getCanvas().style.cursor = 'pointer'
    const p = e.features[0].properties
    hoveredRoute.value = p
    map.setPaintProperty('routes-base', 'line-opacity', ['case', ['==', ['get', 'id'], p.id], 0.8, 0.3])
    map.setPaintProperty('routes-dash', 'line-width',   ['case', ['==', ['get', 'id'], p.id], 3, 2])
  })
  map.on('mouseleave', 'routes-hitarea', () => {
    map.getCanvas().style.cursor = ''
    hoveredRoute.value = null
    map.setPaintProperty('routes-base', 'line-opacity', 0.3)
    map.setPaintProperty('routes-dash', 'line-width', 2)
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

  layersReady = true
  animateDash()
}

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

onMounted(() => {
  maptilersdk.config.apiKey = MAPTILER_KEY

  map = new maptilersdk.Map({
    container: mapContainer.value,
    style:     `https://api.maptiler.com/maps/ocean/style.json?key=${MAPTILER_KEY}`,
    center:    [0, 20],
    zoom:      1.8,
    projection: 'globe',
    attributionControl: false,
  })


  map.on('load', () => {
    initLayers()
  })
})

onUnmounted(() => {
  if (animationFrame) clearTimeout(animationFrame)
  if (popup) popup.remove()
  if (map) map.remove()
})

watch(() => props.sightings, (val) => {
  if (layersReady && map?.getSource('sightings'))
    map.getSource('sightings').setData(sightingsGeoJSON(val))
}, { deep: true })

watch(() => props.migrationRoutes, (val) => {
  if (layersReady && map?.getSource('routes')) {
    map.getSource('routes').setData(routesGeoJSON(val))
    map.getSource('route-endpoints').setData(routeEndpointsGeoJSON(val))
  }
}, { deep: true })
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
.route-tag {
  font-size: 10px; padding: 2px 8px; border-radius: 20px;
  background: rgba(0,229,255,0.08); border: 1px solid rgba(0,229,255,0.15);
  color: var(--text-secondary); text-transform: capitalize; font-family: var(--font-mono);
}
.route-panel-path { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; font-size: 11px; }
.route-origin, .route-dest { color: var(--text-primary); font-weight: 500; }
.route-arrow { color: var(--cyan); flex-shrink: 0; }
.route-panel-desc { font-size: 11px; color: var(--text-secondary); line-height: 1.7; }
.panel-enter-active, .panel-leave-active { transition: all 0.2s ease; }
.panel-enter-from, .panel-leave-to { opacity: 0; transform: translateY(8px); }
</style>
