<template>
  <div class="app">

    <!-- Desktop sidebar -->
    <Sidebar
      v-if="!isMobile"
      :speciesList="speciesSummary"
      :totalCount="totalCount"
      :filteredCount="shownCount"
      :selectedSpecies="selectedSpecies"
      :loading="loading"
      @species-change="onSpeciesChange"
    />

    <!-- Mobile: hamburger (only when sheet closed) -->
    <button v-if="isMobile && !sheetOpen && !infoOpen" class="hamburger" @click="sheetOpen = true">☰</button>

    <!-- Mobile: info button (only when species selected and sheets closed) -->
    <button
      v-if="isMobile && selectedSpecies && !sheetOpen && !infoOpen"
      class="info-btn"
      :style="{ borderColor: speciesColor(selectedSpecies), color: speciesColor(selectedSpecies) }"
      @click="infoOpen = true"
    >ⓘ</button>

    <!-- Mobile: bottom sheet -->
    <Transition name="sheet">
      <div v-if="isMobile && sheetOpen" class="mobile-sheet">
        <div class="sheet-header">
          <div class="sheet-brand">
            <span>🐋</span>
            <span class="sheet-brand-title">whaledata<span class="sheet-brand-tld">.org</span></span>
          </div>
          <button class="sheet-close" @click="sheetOpen = false">✕</button>
        </div>

        <div class="sheet-stats">
          <div class="sheet-stat">
            <span class="sheet-stat-value">{{ totalCount.toLocaleString() }}</span>
            <span class="sheet-stat-label">sightings</span>
          </div>
          <div class="sheet-stat-divider" />
          <div class="sheet-stat">
            <span class="sheet-stat-value">{{ speciesSummary.length }}</span>
            <span class="sheet-stat-label">species</span>
          </div>
          <div class="sheet-stat-divider" />
          <div class="sheet-stat">
            <span class="sheet-stat-value">{{ shownCount.toLocaleString() }}</span>
            <span class="sheet-stat-label">shown</span>
          </div>
        </div>

        <div class="sheet-label">Layers</div>
        <div style="display:flex;gap:8px;padding:0 12px 12px;flex-wrap:wrap">
          <button class="sheet-layer-btn" :class="{ active: activeLayers.strandings }" @click="activeLayers.strandings = !activeLayers.strandings">🔴 Strandings</button>
          <button class="sheet-layer-btn" :class="{ active: activeLayers.inaturalist }" @click="activeLayers.inaturalist = !activeLayers.inaturalist">🟢 iNaturalist</button>
          <button class="sheet-layer-btn" :class="{ active: activeLayers.historical }" @click="activeLayers.historical = !activeLayers.historical">🟡 Historical</button>
          <button class="sheet-layer-btn" :class="{ active: activeConservation.feeding }" @click="activeConservation.feeding = !activeConservation.feeding">🌿 Feeding</button>
          <button class="sheet-layer-btn" :class="{ active: activeConservation.sonar }" @click="activeConservation.sonar = !activeConservation.sonar">⚠️ Sonar</button>
        </div>

        <div class="sheet-label">Species</div>
        <div class="sheet-species-list">
          <button
            class="sheet-species-btn"
            :class="{ active: selectedSpecies === '' }"
            @click="onSpeciesChange('')"
          >
            <span class="sheet-dot all-dot" />
            All species
          </button>
          <button
            v-for="s in speciesSummary"
            :key="s.common_name"
            class="sheet-species-btn"
            :class="{ active: selectedSpecies === s.common_name }"
            @click="onSpeciesChange(s.common_name)"
          >
            <span class="sheet-dot" :style="{ background: speciesColor(s.common_name) }" />
            <span class="sheet-species-name">{{ s.common_name }}</span>
            <span class="sheet-species-count">{{ s.sighting_count.toLocaleString() }}</span>
          </button>
        </div>
      </div>
    </Transition>

    <!-- Species detail sheet -->
    <Transition name="sheet">
      <div v-if="isMobile && infoOpen && activeSpeciesData" class="mobile-sheet info-sheet">
        <div class="sheet-header">
          <div class="sheet-brand" :style="{ color: speciesColor(selectedSpecies) }">
            {{ selectedSpecies }}
          </div>
          <button class="sheet-close" @click="infoOpen = false">✕</button>
        </div>
        <div class="info-scroll">
          <img :src="activeSpeciesData.photo" :alt="selectedSpecies" class="info-img" @error="e => e.target.style.display='none'" />
          <div class="info-body">
            <div class="info-sci">{{ activeSpeciesData.scientific }}</div>
            <div class="info-badges">
              <span class="iucn-badge" :class="activeSpeciesData.iucn.toLowerCase()">{{ activeSpeciesData.iucn }}</span>
              <span class="iucn-label">{{ activeSpeciesData.iucnLabel }}</span>
            </div>
            <div class="info-facts">
              <div v-for="f in activeSpeciesData.facts" :key="f.label" class="info-fact">
                <span class="info-fact-value">{{ f.value }}</span>
                <span class="info-fact-label">{{ f.label }}</span>
              </div>
            </div>
            <p class="info-desc">{{ activeSpeciesData.description }}</p>
            <div class="info-audio-label">🔊 Whale call</div>
            <audio :key="activeSpeciesData.audio" controls preload="none" class="info-audio">
              <source :src="activeSpeciesData.audio" type="audio/ogg" />
            </audio>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Backdrop -->
    <div v-if="isMobile && (sheetOpen || infoOpen)" class="backdrop" @click="sheetOpen = false; infoOpen = false" />

    <!-- Mobile stats bar (always visible) -->
    <div v-if="isMobile" class="mobile-bar">
      <span class="bar-stat"><b>{{ totalCount.toLocaleString() }}</b> sightings</span>
      <span class="bar-divider" />
      <span class="bar-stat"><b>{{ speciesSummary.length }}</b> species</span>
      <span class="bar-divider" />
      <span class="bar-stat" :style="{ color: selectedSpecies ? speciesColor(selectedSpecies) : 'var(--text-secondary)' }">
        {{ selectedSpecies || 'All species' }}
      </span>
    </div>

    <!-- Mobile action row -->
    <div v-if="isMobile" class="mobile-actions">
      <button class="mob-btn" @click="shareMap">{{ shareCopied ? '✓' : '🔗' }}</button>
      <button class="mob-btn" @click="nearMe">📍</button>
      <button class="mob-btn" :class="{ active: yearOpen }" @click="yearOpen = !yearOpen">📅</button>
    </div>

    <!-- Mobile year popup -->
    <Transition name="layers-panel">
      <div v-if="isMobile && yearOpen" class="mobile-year-popup">
        <div class="year-popup-header">
          <span class="year-popup-title">{{ yearRange[0] }} – {{ yearRange[1] }}</span>
          <div style="display:flex;gap:8px;align-items:center">
            <span class="year-reset-link" @click="yearRange = [1900, 2026]">Reset</span>
            <button class="lp-close-btn" @click="yearOpen = false">✕</button>
          </div>
        </div>
        <div class="year-slider-track" style="margin-top:8px">
          <div class="year-slider-fill" :style="fillStyle"></div>
          <input type="range" min="1900" max="2026" :value="yearRange[0]"
            @input="e => yearRange = [Math.min(parseInt(e.target.value), yearRange[1] - 1), yearRange[1]]"
            class="year-slider year-slider-min" />
          <input type="range" min="1900" max="2026" :value="yearRange[1]"
            @input="e => yearRange = [yearRange[0], Math.max(parseInt(e.target.value), yearRange[0] + 1)]"
            class="year-slider year-slider-max" />
        </div>
      </div>
    </Transition>

    <!-- Top-right action bar — desktop -->
    <div v-if="!isMobile" class="top-actions">
      <button class="top-btn btn-share" @click="shareMap">
        {{ shareCopied ? '✓ Copied!' : '🔗 Share' }}
      </button>
      <button class="top-btn btn-nearme" @click="nearMe" :class="{ loading: nearMeLoading }">
        {{ nearMeLoading ? '...' : '📍 Near me' }}
      </button>
    </div>

    <!-- Year filter button + popup — desktop -->
    <div v-if="!isMobile" class="year-btn-wrap">
      <button class="bottom-btn btn-year" :class="{ active: yearOpen, filtered: yearRange[0] !== 1900 || yearRange[1] !== 2026 }" @click="yearOpen = !yearOpen">
        📅 {{ yearRange[0] }} – {{ yearRange[1] }}
        <span v-if="yearRange[0] !== 1900 || yearRange[1] !== 2026" class="year-filtered-dot"></span>
      </button>
      <Transition name="layers-panel">
        <div v-if="yearOpen" class="year-popup">
          <div class="year-popup-header">
            <span class="year-popup-title">Year Range</span>
            <div style="display:flex;gap:8px;align-items:center">
              <span class="year-reset-link" @click="yearRange = [1900, 2026]">Reset</span>
              <button class="lp-close-btn" @click="yearOpen = false">✕</button>
            </div>
          </div>
          <div class="year-popup-values">
            <span class="year-val">{{ yearRange[0] }}</span>
            <span class="year-sep">–</span>
            <span class="year-val">{{ yearRange[1] }}</span>
          </div>
          <div class="year-slider-track">
            <div class="year-slider-fill" :style="fillStyle"></div>
            <input type="range" min="1900" max="2026" :value="yearRange[0]"
              @input="e => yearRange = [Math.min(parseInt(e.target.value), yearRange[1] - 1), yearRange[1]]"
              class="year-slider year-slider-min" />
            <input type="range" min="1900" max="2026" :value="yearRange[1]"
              @input="e => yearRange = [yearRange[0], Math.max(parseInt(e.target.value), yearRange[0] + 1)]"
              class="year-slider year-slider-max" />
          </div>
        </div>
      </Transition>
    </div>

    <LayersPanel
      v-model="activeLayers"
      v-model:conservationValue="activeConservation"
      :layersSummary="layersSummary"
      :selectedSpecies="selectedSpecies"
    />

    <div class="map-area">
      <GlobeMap
        :sightings="filteredSightings"
        :migrationRoutes="filteredRoutes"
        :selectedSpecies="selectedSpecies"
        :yearRange="yearRange"
        :activeLayers="activeLayers"
        :layerData="filteredLayerData"
        :activeConservation="activeConservation"
        :userLocation="userLocation"
        :globeRotating="globeRotating"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import GlobeMap from './components/GlobeMap.vue'
import Sidebar from './components/Sidebar.vue'
import LayersPanel from './components/LayersPanel.vue'

const API_URL = import.meta.env.VITE_API_URL || 'https://api.whaledata.org'

const allSightings    = ref([])
const allRoutes       = ref([])
const speciesSummary  = ref([])
const selectedSpecies = ref('')
const loading         = ref(true)
const isMobile        = ref(false)
const yearRange       = ref([1990, 2026])
const layersSummary   = ref({})
const activeLayers    = ref({
  sightings:   true,
  strandings:  false,
  acoustics:   false,
  inaturalist: false,
  historical:  false,
})
const activeConservation = ref({ feeding: false, sonar: false })
const shareCopied    = ref(false)
const yearOpen       = ref(false)
const nearMeLoading  = ref(false)
const layerData = ref({
  strandings:  [],
  acoustics:   [],
  inaturalist: [],
  historical:  [],
})

const fillStyle = computed(() => {
  const min = 1900, max = 2026, range = max - min
  const left  = ((yearRange.value[0] - min) / range) * 100
  const right = ((yearRange.value[1] - min) / range) * 100
  return { left: left + '%', width: (right - left) + '%' }
})
const sheetOpen       = ref(false)
const infoOpen        = ref(false)

const SPECIES_DATA = {
  'Humpback whale': {
    scientific: 'Megaptera novaeangliae', iucn: 'LC', iucnLabel: 'Least Concern',
    photo: '/assets/images/humpback.jpg',
    description: 'Famous for their haunting, complex songs sung only by males. Humpbacks make one of the longest migrations of any mammal, travelling up to 8,000 km between feeding and breeding grounds.',
    facts: [{ label: 'Length', value: '14–17m' }, { label: 'Weight', value: '25–30t' }, { label: 'Lifespan', value: '45–100yr' }],
    audio: '/assets/sounds/humpback.ogg'
  },
  'Blue whale': {
    scientific: 'Balaenoptera musculus', iucn: 'EN', iucnLabel: 'Endangered',
    photo: '/assets/images/blue-whale.jpg',
    description: "The largest animal ever known to have existed on Earth. A blue whale's heart alone weighs as much as a car, and its call can be heard up to 1,600 km away.",
    facts: [{ label: 'Length', value: '24–33m' }, { label: 'Weight', value: 'up to 200t' }, { label: 'Lifespan', value: '80–90yr' }],
    audio: '/assets/sounds/blue-whale.ogg'
  },
  'Grey whale': {
    scientific: 'Eschrichtius robustus', iucn: 'LC', iucnLabel: 'Least Concern',
    photo: '/assets/images/grey-whale.jpg',
    description: 'Undertakes the longest migration of any mammal — up to 20,000 km round trip between Arctic feeding grounds and warm Mexican lagoons.',
    facts: [{ label: 'Length', value: '13–15m' }, { label: 'Weight', value: '15–35t' }, { label: 'Migration', value: '20,000km' }],
    audio: '/assets/sounds/grey-whale.ogg'
  },
  'Sperm whale': {
    scientific: 'Physeter macrocephalus', iucn: 'VU', iucnLabel: 'Vulnerable',
    photo: '/assets/images/sperm-whale.jpg',
    description: 'The largest toothed predator on Earth, capable of diving to 3,000m for over 90 minutes. Their clicks are the loudest sounds made by any animal.',
    facts: [{ label: 'Length', value: '15–20m' }, { label: 'Dive', value: '3,000m' }, { label: 'Lifespan', value: '60–70yr' }],
    audio: '/assets/sounds/sperm-whale.ogg'
  },
  'Fin whale': {
    scientific: 'Balaenoptera physalus', iucn: 'VU', iucnLabel: 'Vulnerable',
    photo: '/assets/images/fin-whale.jpg',
    description: 'The second largest animal on Earth, known as the "greyhound of the sea" for its slender build and speed.',
    facts: [{ label: 'Length', value: '18–26m' }, { label: 'Speed', value: '37 km/h' }, { label: 'Lifespan', value: '80–90yr' }],
    audio: '/assets/sounds/fin-whale.ogg'
  },
  'Orca': {
    scientific: 'Orcinus orca', iucn: 'DD', iucnLabel: 'Data Deficient',
    photo: '/assets/images/orca.jpg',
    description: 'The apex predator of the ocean, found in every sea from Arctic to Antarctic. Orcas live in tight family pods with distinct cultural traditions.',
    facts: [{ label: 'Length', value: '6–8m' }, { label: 'Weight', value: '3–6t' }, { label: 'Lifespan', value: '50–90yr' }],
    audio: '/assets/sounds/orca.ogg'
  }
}

const activeSpeciesData = computed(() => selectedSpecies.value ? SPECIES_DATA[selectedSpecies.value] : null)

const filteredLayerData = computed(() => {
  const species = selectedSpecies.value
  const result  = {}
  for (const key of ['strandings','acoustics','inaturalist','historical']) {
    let data = (layerData.value[key] || []).filter(r => {
      if (r.longitude == null || r.latitude == null) return false
      // Reuse ocean filter — layer data uses same lat/lng fields
      return isOceanSighting({ longitude: r.longitude, latitude: r.latitude })
    })
    if (species) data = data.filter(r => r.common_name === species)
    result[key] = data
  }
  return result
})

const SPECIES_COLORS = {
  'Humpback whale': '#00e5ff',
  'Blue whale':     '#4d9fff',
  'Grey whale':     '#a8c5da',
  'Sperm whale':    '#7eb8d4',
  'Fin whale':      '#5dd4b8',
  'Orca':           '#ff6b9d',
}
function speciesColor(name) { return SPECIES_COLORS[name] || '#ffffff' }

function checkMobile() { isMobile.value = window.innerWidth < 768 }

const totalCount = computed(() => {
  let n = allSightings.value.filter(isOceanSighting).length
  for (const key of ['strandings','acoustics','inaturalist','historical']) {
    if (activeLayers.value[key]) n += (layerData.value[key] || []).length
  }
  return n
})

function isOceanSighting(s) {
  const lng = parseFloat(s.longitude)
  const lat = parseFloat(s.latitude)
  if (lng > -72 && lng < -44 && lat > -18 && lat < 8)   return false
  if (lng > -68 && lng < -52 && lat > -28 && lat < -15)  return false
  if (lng > 70  && lng < 100 && lat > 22  && lat < 38)   return false
  if (lng > 50  && lng < 120 && lat > 38  && lat < 58)   return false
  if (lng > 10  && lng < 40  && lat > 5   && lat < 22)   return false
  return true
}

const filteredSightings = computed(() => {
  const base = allSightings.value.filter(isOceanSighting)
  if (!selectedSpecies.value) return base
  return base.filter(s => s.common_name === selectedSpecies.value)
})

const shownCount = computed(() => {
  let n = filteredSightings.value.length
  for (const key of ['strandings','acoustics','inaturalist','historical']) {
    if (activeLayers.value[key]) {
      const data = filteredLayerData.value[key] || []
      n += data.length
    }
  }
  return n
})

const filteredRoutes = computed(() => {
  if (!selectedSpecies.value) return allRoutes.value
  return allRoutes.value.filter(r => r.common_name === selectedSpecies.value)
})

function onSpeciesChange(species) {
  selectedSpecies.value = species
  sheetOpen.value = false
  infoOpen.value = false
}

async function loadData() {
  loading.value = true
  try {
    const [a, b, c, d] = await Promise.all([
      fetch(`${API_URL}/sightings/?limit=5000`),
      fetch(`${API_URL}/sightings/species-summary`),
      fetch(`${API_URL}/routes/`),
      fetch(`${API_URL}/layers/summary`),
    ])
    allSightings.value   = (await a.json()).data || []
    speciesSummary.value = (await b.json()).data || []
    allRoutes.value      = (await c.json()).data || []
    layersSummary.value  = (await d.json()).layers || {}
  } catch (err) {
    console.error('Failed to load whale data:', err)
  } finally {
    loading.value = false
  }
}

async function loadLayerData(key, url) {
  try {
    const res = await fetch(`${API_URL}${url}?limit=5000`)
    const data = await res.json()
    layerData.value[key] = data.data || []
  } catch (err) {
    console.error(`Failed to load ${key}:`, err)
  }
}

// Watch activeLayers — fetch data when a layer is turned on

// ── Share ─────────────────────────────────────────────────────
function shareMap() {
  const params = new URLSearchParams()
  if (selectedSpecies.value) params.set('species', selectedSpecies.value)
  if (yearRange.value[0] !== 1990) params.set('from', yearRange.value[0])
  if (yearRange.value[1] !== 2026) params.set('to', yearRange.value[1])
  const activeLayers_ = Object.entries(activeLayers.value)
    .filter(([k, v]) => v && k !== 'sightings')
    .map(([k]) => k).join(',')
  if (activeLayers_) params.set('layers', activeLayers_)
  const url = `${window.location.origin}${window.location.pathname}?${params.toString()}`
  navigator.clipboard.writeText(url).then(() => {
    shareCopied.value = true
    setTimeout(() => shareCopied.value = false, 2500)
  })
}

// ── Near Me ───────────────────────────────────────────────────
function nearMe() {
  if (!navigator.geolocation) return
  nearMeLoading.value = true
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      nearMeLoading.value = false
      // Emit to GlobeMap to fly to user location
      userLocation.value = { lng: pos.coords.longitude, lat: pos.coords.latitude }
    },
    () => { nearMeLoading.value = false }
  )
}
const userLocation = ref(null)

// ── URL state restore ─────────────────────────────────────────
function restoreFromURL() {
  const params = new URLSearchParams(window.location.search)
  if (params.get('species')) selectedSpecies.value = params.get('species')
  if (params.get('from'))    yearRange.value[0] = parseInt(params.get('from'))
  if (params.get('to'))      yearRange.value[1] = parseInt(params.get('to'))
  if (params.get('layers')) {
    params.get('layers').split(',').forEach(k => {
      if (activeLayers.value.hasOwnProperty(k)) activeLayers.value[k] = true
    })
  }
}

// ── Keyboard shortcuts ────────────────────────────────────────
const SPECIES_KEYS = {
  '1': 'Humpback whale', '2': 'Blue whale', '3': 'Grey whale',
  '4': 'Sperm whale',    '5': 'Fin whale',  '6': 'Orca',
}
function onKeydown(e) {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return
  if (SPECIES_KEYS[e.key]) { onSpeciesChange(SPECIES_KEYS[e.key]); return }
  if (e.key === '0') { onSpeciesChange(''); return }
  if (e.key === 'Escape') { sheetOpen.value = false; infoOpen.value = false; return }
  if (e.key === ' ') { e.preventDefault(); globeRotating.value = !globeRotating.value; return }
}
const globeRotating = ref(true)

const LAYER_URLS = {
  strandings:  '/strandings/',
  acoustics:   '/acoustics/',
  inaturalist: '/inaturalist/',
  historical:  '/historical/',
}

watch(activeLayers, (layers) => {
  for (const [key, active] of Object.entries(layers)) {
    if (active && key !== 'sightings' && layerData.value[key]?.length === 0) {
      loadLayerData(key, LAYER_URLS[key])
    }
  }
}, { deep: true })

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  window.addEventListener('keydown', onKeydown)
  restoreFromURL()
  loadData()
})
onUnmounted(() => { window.removeEventListener('resize', checkMobile); window.removeEventListener('keydown', onKeydown) })
</script>

<style scoped>
.app { width: 100vw; height: 100vh; overflow: hidden; position: relative; }
.map-area { position: absolute; inset: 0; }

/* ── Hamburger ─────────────────────────────────────────────── */
.hamburger {
  position: fixed;
  top: 16px; left: 16px;
  z-index: 500;
  width: 44px; height: 44px;
  border-radius: 12px;
  background: rgba(8, 13, 26, 0.92);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border-bright);
  color: var(--cyan);
  font-size: 20px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}

/* ── Mobile sheet ──────────────────────────────────────────── */
.mobile-sheet {
  position: fixed;
  bottom: 64px; /* sit above mobile bar */
  left: 0; right: 0;
  max-height: 80vh;
  background: rgba(8, 13, 26, 0.98);
  backdrop-filter: blur(24px);
  border-top: 1px solid var(--border-bright);
  border-radius: 20px 20px 0 0;
  z-index: 400;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sheet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 20px 12px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.sheet-brand {
  display: flex; align-items: center; gap: 8px;
  font-size: 16px; font-weight: 700; color: var(--text-primary);
}
.sheet-brand-tld { color: var(--cyan); }

.sheet-close {
  width: 32px; height: 32px;
  border-radius: 8px;
  background: none;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}

.sheet-stats {
  display: flex; align-items: center; gap: 16px;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.sheet-stat { display: flex; flex-direction: column; align-items: center; flex: 1; }
.sheet-stat-value { font-size: 16px; font-weight: 700; color: var(--cyan); font-family: var(--font-mono); }
.sheet-stat-label { font-size: 9px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2px; }
.sheet-stat-divider { width: 1px; height: 28px; background: var(--border); }

.sheet-label {
  font-size: 9px; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.12em;
  padding: 12px 20px 6px;
  flex-shrink: 0;
}

.sheet-species-list {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding: 0 12px 20px;
  flex: 1;
}

.sheet-species-btn {
  display: flex; align-items: center; gap: 10px;
  width: 100%; background: none;
  border: 1px solid transparent; border-radius: 10px;
  padding: 12px 10px; margin-bottom: 4px;
  cursor: pointer; color: var(--text-secondary);
  font-family: var(--font-display); font-size: 15px;
  text-align: left; transition: all 0.15s;
}
.sheet-species-btn.active {
  background: var(--cyan-glow-soft);
  border-color: var(--border-bright);
  color: var(--text-primary);
}
.sheet-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.all-dot {
  background: conic-gradient(
    #00e5ff 0deg 60deg, #4d9fff 60deg 120deg, #a8c5da 120deg 180deg,
    #7eb8d4 180deg 240deg, #5dd4b8 240deg 300deg, #ff6b9d 300deg 360deg
  );
}
.sheet-layer-btn {
  padding: 7px 12px; border-radius: 20px; font-size: 12px;
  background: none; border: 1px solid var(--border);
  color: var(--text-secondary); cursor: pointer; font-family: var(--font-display);
  transition: all 0.15s;
}
.sheet-layer-btn.active {
  background: var(--cyan-glow-soft); border-color: var(--border-bright);
  color: var(--text-primary);
}
.sheet-species-name { flex: 1; }
.sheet-species-count { font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); }

/* ── Backdrop ──────────────────────────────────────────────── */
.backdrop {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 399;
}

/* ── Mobile stats bar ──────────────────────────────────────── */
.mobile-bar {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  height: 64px;
  background: rgba(8, 13, 26, 0.95);
  backdrop-filter: blur(20px);
  border-top: 1px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  gap: 12px;
  z-index: 300;
  pointer-events: none;
}
.bar-stat { font-size: 12px; color: var(--text-secondary); }
.bar-stat b { color: var(--cyan); font-family: var(--font-mono); }
.bar-divider { width: 1px; height: 16px; background: var(--border); }

/* ── Mobile action row ──────────────────────────────────────── */
.mobile-actions {
  position: fixed;
  bottom: 65px;
  right: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 300;
}
.mob-btn {
  width: 40px; height: 40px;
  border-radius: 12px;
  background: rgba(8, 13, 26, 0.92);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border-bright);
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.mob-btn.active, .mob-btn:hover {
  background: rgba(0, 229, 255, 0.1);
  border-color: rgba(0, 229, 255, 0.4);
  color: var(--cyan);
}
.mobile-year-popup {
  position: fixed;
  bottom: 220px;
  right: 12px;
  width: 240px;
  background: rgba(8, 13, 26, 0.97);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(0, 229, 255, 0.2);
  border-radius: 14px;
  padding: 14px 16px 16px;
  z-index: 400;
}

/* ── Info button ───────────────────────────────────────────── */
.info-btn {
  position: fixed;
  top: 16px; left: 68px;
  z-index: 500;
  width: 44px; height: 44px;
  border-radius: 12px;
  background: rgba(8, 13, 26, 0.92);
  backdrop-filter: blur(12px);
  border: 1px solid;
  font-size: 20px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}

/* ── Info sheet ─────────────────────────────────────────────── */
.info-sheet { bottom: 0 !important; }

.info-scroll {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  flex: 1;
}

.info-img {
  width: 100%;
  height: 180px;
  object-fit: cover;
  display: block;
}

.info-body { padding: 16px 20px 32px; }

.info-sci {
  font-size: 12px; color: var(--text-muted);
  font-style: italic; margin-bottom: 10px;
}

.info-badges { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
.iucn-badge {
  font-size: 10px; font-weight: 700; padding: 2px 8px;
  border-radius: 4px; font-family: var(--font-mono);
}
.iucn-badge.lc  { background: rgba(0,180,100,0.2); color: #00b464; border: 1px solid rgba(0,180,100,0.3); }
.iucn-badge.en  { background: rgba(255,140,0,0.2); color: #ff8c00; border: 1px solid rgba(255,140,0,0.3); }
.iucn-badge.vu  { background: rgba(255,200,0,0.2); color: #ffc800; border: 1px solid rgba(255,200,0,0.3); }
.iucn-badge.dd  { background: rgba(150,150,180,0.2); color: #9696b4; border: 1px solid rgba(150,150,180,0.3); }
.iucn-label { font-size: 11px; color: var(--text-muted); }

.info-facts {
  display: flex; justify-content: space-around;
  padding: 12px 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);
  margin-bottom: 14px;
}
.info-fact { display: flex; flex-direction: column; align-items: center; gap: 3px; }
.info-fact-value { font-size: 14px; font-weight: 600; color: var(--text-primary); font-family: var(--font-mono); }
.info-fact-label { font-size: 9px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; }

.info-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.7; margin-bottom: 16px; }
.info-audio-label { font-size: 10px; color: var(--text-muted); margin-bottom: 6px; }
.info-audio { width: 100%; height: 36px; filter: invert(1) hue-rotate(180deg) brightness(0.8); }

/* ── Sheet transition ───────────────────────────────────────── */
.sheet-enter-active, .sheet-leave-active {
  transition: transform 0.32s cubic-bezier(0.32, 0.72, 0, 1);
}
.sheet-enter-from, .sheet-leave-to { transform: translateY(100%); }
/* ── Bottom button base (year filter) ──────────────────────── */
.bottom-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 10px 18px;
  background: rgba(8, 13, 26, 0.92);
  backdrop-filter: blur(16px);
  border-radius: 30px;
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.bottom-btn.loading { opacity: 0.6; cursor: wait; }

/* ── Top-right actions ──────────────────────────────────────── */
.top-actions {
  position: fixed;
  top: 16px;
  right: 56px; /* clear MapTiler controls */
  display: flex;
  gap: 8px;
  z-index: 200;
}

.top-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 9px 16px;
  background: rgba(8, 13, 26, 0.92);
  backdrop-filter: blur(16px);
  border-radius: 30px;
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.top-btn.loading { opacity: 0.6; cursor: wait; }

/* Share — purple */
.btn-share {
  border: 1px solid rgba(180, 100, 255, 0.3);
  color: rgba(180, 100, 255, 0.8);
}
.btn-share:hover {
  background: rgba(180, 100, 255, 0.1);
  border-color: rgba(180, 100, 255, 0.6);
  color: #b464ff;
  box-shadow: 0 0 16px rgba(180, 100, 255, 0.15);
}

/* Near me — blue */
.btn-nearme {
  border: 1px solid rgba(77, 159, 255, 0.3);
  color: rgba(77, 159, 255, 0.8);
}
.btn-nearme:hover {
  background: rgba(77, 159, 255, 0.1);
  border-color: rgba(77, 159, 255, 0.6);
  color: #4d9fff;
  box-shadow: 0 0 16px rgba(77, 159, 255, 0.15);
}

/* ── Year filter button + popup ────────────────────────────── */
.year-btn-wrap {
  position: fixed;
  bottom: 32px;
  right: 24px;
  z-index: 200;
}

.btn-year {
  border: 1px solid rgba(0, 229, 255, 0.25);
  color: rgba(0, 229, 255, 0.7);
  font-family: var(--font-mono);
  position: relative;
}
.btn-year:hover, .btn-year.active {
  background: rgba(0, 229, 255, 0.1);
  border-color: rgba(0, 229, 255, 0.5);
  color: #00e5ff;
  box-shadow: 0 0 16px rgba(0, 229, 255, 0.15);
}
.btn-year.filtered {
  border-color: rgba(0, 229, 255, 0.5);
  color: #00e5ff;
}
.year-filtered-dot {
  width: 6px; height: 6px;
  background: var(--cyan);
  border-radius: 50%;
  margin-left: 2px;
}

.year-popup {
  position: absolute;
  bottom: calc(100% + 10px);
  right: 0;
  width: 260px;
  background: rgba(8, 13, 26, 0.97);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(0, 229, 255, 0.2);
  border-radius: 14px;
  padding: 14px 16px 16px;
  box-shadow: 0 0 30px rgba(0, 229, 255, 0.08);
}

.year-popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.year-popup-title {
  font-size: 10px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
}
.year-reset-link {
  font-size: 11px;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.15s;
}
.year-reset-link:hover { color: var(--cyan); }
.lp-close-btn {
  width: 22px; height: 22px;
  background: none;
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-muted);
  font-size: 11px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}

.year-popup-values {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 12px;
}
.year-val {
  font-size: 20px;
  font-weight: 700;
  color: var(--cyan);
  font-family: var(--font-mono);
  line-height: 1;
}
.year-sep { font-size: 14px; color: var(--text-muted); }

.year-slider-track {
  position: relative;
  height: 20px;
  display: flex;
  align-items: center;
}
.year-slider-track::before {
  content: '';
  position: absolute;
  left: 0; right: 0; height: 3px;
  background: var(--border);
  border-radius: 2px;
  top: 50%; transform: translateY(-50%);
}
.year-slider-fill {
  position: absolute;
  height: 3px;
  background: var(--cyan);
  border-radius: 2px;
  top: 50%; transform: translateY(-50%);
  opacity: 0.6;
  pointer-events: none;
}
.year-slider {
  position: absolute;
  left: 0; right: 0;
  -webkit-appearance: none;
  width: 100%; height: 3px;
  background: transparent;
  outline: none;
  cursor: pointer;
  pointer-events: none;
}
.year-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px; height: 16px;
  border-radius: 50%;
  background: var(--cyan);
  cursor: pointer;
  border: 2px solid #080d1a;
  box-shadow: 0 0 8px rgba(0, 229, 255, 0.5);
  pointer-events: auto;
  position: relative; z-index: 1;
}
.year-slider::-moz-range-thumb {
  width: 16px; height: 16px;
  border-radius: 50%;
  background: var(--cyan);
  cursor: pointer;
  border: 2px solid #080d1a;
  box-shadow: 0 0 8px rgba(0, 229, 255, 0.5);
  pointer-events: auto;
}
</style>
