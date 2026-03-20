<template>
  <div class="app">

    <!-- Desktop sidebar -->
    <Sidebar
      v-if="!isMobile"
      :speciesList="speciesSummary"
      :totalCount="totalCount"
      :filteredCount="filteredSightings.length"
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
            <span class="sheet-stat-value">{{ filteredSightings.length.toLocaleString() }}</span>
            <span class="sheet-stat-label">shown</span>
          </div>
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

    <!-- Year range slider — desktop -->
    <div v-if="!isMobile" class="year-slider-wrap">
      <div class="year-slider-label">
        <span>📅 {{ yearRange[0] }}</span>
        <span class="year-slider-title">Year Range</span>
        <span>{{ yearRange[1] }}</span>
      </div>
      <div class="year-slider-track">
        <input type="range" min="1900" max="2026" :value="yearRange[0]"
          @input="e => yearRange = [parseInt(e.target.value), yearRange[1]]"
          class="year-slider" />
        <input type="range" min="1900" max="2026" :value="yearRange[1]"
          @input="e => yearRange = [yearRange[0], parseInt(e.target.value)]"
          class="year-slider" />
      </div>
    </div>

    <div class="map-area">
      <GlobeMap
        :sightings="filteredSightings"
        :migrationRoutes="filteredRoutes"
        :selectedSpecies="selectedSpecies"
        :yearRange="yearRange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import GlobeMap from './components/GlobeMap.vue'
import Sidebar from './components/Sidebar.vue'

const API_URL = import.meta.env.VITE_API_URL || 'https://api.whaledata.org'

const allSightings    = ref([])
const allRoutes       = ref([])
const speciesSummary  = ref([])
const selectedSpecies = ref('')
const loading         = ref(true)
const isMobile        = ref(false)
const yearRange       = ref([1990, 2026])
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

const totalCount = computed(() => allSightings.value.filter(isOceanSighting).length)

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
    const [a, b, c] = await Promise.all([
      fetch(`${API_URL}/sightings/?limit=5000`),
      fetch(`${API_URL}/sightings/species-summary`),
      fetch(`${API_URL}/routes/`)
    ])
    allSightings.value   = (await a.json()).data || []
    speciesSummary.value = (await b.json()).data || []
    allRoutes.value      = (await c.json()).data || []
  } catch (err) {
    console.error('Failed to load whale data:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => { checkMobile(); window.addEventListener('resize', checkMobile); loadData() })
onUnmounted(() => window.removeEventListener('resize', checkMobile))
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
/* ── Year range slider ─────────────────────────────────────── */
.year-slider-wrap {
  position: fixed;
  bottom: 32px;
  right: 80px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  z-index: 150;
  pointer-events: none;
}

.year-slider-label {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-secondary);
  background: rgba(8, 13, 26, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 4px 14px;
  pointer-events: auto;
}

.year-slider-title {
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.year-slider-track {
  display: flex;
  gap: 8px;
  align-items: center;
  background: rgba(8, 13, 26, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 6px 16px;
  pointer-events: auto;
}

.year-slider {
  -webkit-appearance: none;
  width: 160px;
  height: 3px;
  border-radius: 2px;
  background: var(--border-bright);
  outline: none;
  cursor: pointer;
}
.year-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px; height: 14px;
  border-radius: 50%;
  background: var(--cyan);
  cursor: pointer;
  border: 2px solid var(--bg-deep, #080d1a);
}
.year-slider::-moz-range-thumb {
  width: 14px; height: 14px;
  border-radius: 50%;
  background: var(--cyan);
  cursor: pointer;
  border: 2px solid #080d1a;
}
</style>
