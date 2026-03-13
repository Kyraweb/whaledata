<template>
  <div ref="mapContainer" class="globe-map" />
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

const props = defineProps({
  sightings: { type: Array, default: () => [] },
  selectedSpecies: { type: String, default: '' }
})

const mapContainer = ref(null)
let map = null
let popup = null

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY || ''

const SPECIES_COLORS = {
  'Humpback whale': '#00e5ff',
  'Blue whale':     '#4d9fff',
  'Grey whale':     '#a8c5da',
  'Sperm whale':    '#7eb8d4',
  'Fin whale':      '#5dd4b8',
  'Orca':           '#ff6b9d',
}

function toGeoJSON(sightings) {
  return {
    type: 'FeatureCollection',
    features: sightings
      .filter(s => s.longitude != null && s.latitude != null)
      .map(s => ({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [parseFloat(s.longitude), parseFloat(s.latitude)]
        },
        properties: {
          common_name:     s.common_name || '',
          scientific_name: s.scientific_name || '',
          region:          s.region || '',
          sighted_on:      s.sighted_on || '',
          source:          s.source || '',
          color: SPECIES_COLORS[s.common_name] || '#ffffff'
        }
      }))
  }
}

function updateSource(sightings) {
  if (!map || !map.getSource('sightings')) return
  map.getSource('sightings').setData(toGeoJSON(sightings))
}

function initLayers() {
  map.addSource('sightings', {
    type: 'geojson',
    data: toGeoJSON(props.sightings),
  })

  map.addLayer({
    id: 'sightings-glow',
    type: 'circle',
    source: 'sightings',
    paint: {
      'circle-radius': 10,
      'circle-color': ['get', 'color'],
      'circle-opacity': 0.12,
      'circle-blur': 1
    }
  })

  map.addLayer({
    id: 'sightings-dot',
    type: 'circle',
    source: 'sightings',
    paint: {
      'circle-radius': [
        'interpolate', ['linear'], ['zoom'],
        1, 3,
        5, 5,
        10, 8
      ],
      'circle-color': ['get', 'color'],
      'circle-opacity': 0.85,
      'circle-stroke-width': 0.5,
      'circle-stroke-color': '#ffffff',
      'circle-stroke-opacity': 0.2
    }
  })

  map.on('mouseenter', 'sightings-dot', (e) => {
    map.getCanvas().style.cursor = 'pointer'
    const feature = e.features[0]
    const coords = feature.geometry.coordinates.slice()
    const p = feature.properties
    const color = p.color || '#00e5ff'

    if (popup) popup.remove()

    popup = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 12,
      maxWidth: '240px'
    })
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
    `)
    .addTo(map)
  })

  map.on('mouseleave', 'sightings-dot', () => {
    map.getCanvas().style.cursor = ''
    if (popup) { popup.remove(); popup = null }
  })
}

onMounted(() => {
  map = new maplibregl.Map({
    container: mapContainer.value,
    style: `https://api.maptiler.com/maps/dataviz-dark/style.json?key=${MAPTILER_KEY}`,
    center: [0, 20],
    zoom: 1.8,
    attributionControl: false,
    renderWorldCopies: false
  })

  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')

  map.on('load', () => { initLayers() })
})

onUnmounted(() => {
  if (popup) popup.remove()
  if (map) map.remove()
})

watch(() => props.sightings, (newSightings) => {
  updateSource(newSightings)
}, { deep: true })
</script>

<style scoped>
.globe-map {
  width: 100%;
  height: 100%;
}
</style>
