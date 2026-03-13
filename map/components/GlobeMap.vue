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

const emit = defineEmits(['sighting-click'])

const mapContainer = ref(null)
let map = null
let markers = []

// Maptiler free key — replace with your own from maptiler.com
const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY || 'get_your_own_key'

// Species color map
const SPECIES_COLORS = {
  'Humpback whale': [0, 229, 255],
  'Blue whale':     [77, 159, 255],
  'Grey whale':     [168, 197, 218],
  'Sperm whale':    [126, 184, 212],
  'Fin whale':      [93, 212, 184],
  'Orca':           [255, 107, 157],
}

function getSpeciesColor(commonName) {
  return SPECIES_COLORS[commonName] || [255, 255, 255]
}

function rgbToHex([r, g, b]) {
  return `rgb(${r},${g},${b})`
}

function clearMarkers() {
  markers.forEach(m => m.remove())
  markers = []
}

function renderSightings(sightings) {
  clearMarkers()

  sightings.forEach(s => {
    const lng = parseFloat(s.longitude)
    const lat = parseFloat(s.latitude)
    if (isNaN(lng) || isNaN(lat)) return

    const color = getSpeciesColor(s.common_name)
    const hex = rgbToHex(color)

    // Custom dot marker
    const el = document.createElement('div')
    el.className = 'sighting-dot'
    el.style.cssText = `
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: ${hex};
      box-shadow: 0 0 6px ${hex}, 0 0 12px rgba(${color.join(',')}, 0.4);
      cursor: pointer;
      transition: transform 0.15s ease;
    `
    el.addEventListener('mouseenter', () => {
      el.style.transform = 'scale(1.8)'
    })
    el.addEventListener('mouseleave', () => {
      el.style.transform = 'scale(1)'
    })

    const popup = new maplibregl.Popup({
      offset: [0, -8],
      anchor: 'bottom',
      closeButton: true,
      maxWidth: '240px'
    }).setHTML(`
      <div style="font-family: 'Syne', sans-serif;">
        <div style="font-size: 13px; font-weight: 600; color: ${hex}; margin-bottom: 6px;">
          ${s.common_name}
        </div>
        <div style="font-size: 11px; color: #7a9bb5; font-style: italic; margin-bottom: 8px;">
          ${s.scientific_name || ''}
        </div>
        <div style="font-size: 11px; color: #7a9bb5; line-height: 1.8;">
          ${s.region ? `<span>📍 ${s.region}</span><br/>` : ''}
          ${s.sighted_on ? `<span>📅 ${s.sighted_on}</span><br/>` : ''}
          ${s.source ? `<span>🔬 ${s.source.toUpperCase()}</span>` : ''}
        </div>
      </div>
    `)

    const marker = new maplibregl.Marker({ element: el })
      .setLngLat([lng, lat])
      .setPopup(popup)
      .addTo(map)

    markers.push(marker)
  })
}

onMounted(() => {
  map = new maplibregl.Map({
    container: mapContainer.value,
    style: `https://api.maptiler.com/maps/dataviz-dark/style.json?key=${MAPTILER_KEY}`,
    center: [0, 20],
    zoom: 1.5,
    pitch: 0,
    attributionControl: false,
    renderWorldCopies: false
  })

  map.addControl(new maplibregl.NavigationControl(), 'top-right')

  // Smooth scroll zoom
  map.scrollZoom.setWheelZoomRate(1 / 200)

  map.on('load', () => {
    if (props.sightings.length) {
      renderSightings(props.sightings)
    }
  })
})

onUnmounted(() => {
  clearMarkers()
  if (map) map.remove()
})

watch(() => props.sightings, (newSightings) => {
  if (map && map.loaded()) {
    renderSightings(newSightings)
  }
}, { deep: true })
</script>

<style scoped>
.globe-map {
  width: 100%;
  height: 100%;
}
</style>
