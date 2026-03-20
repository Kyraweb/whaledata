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
    <button v-if="isMobile && !sheetOpen" class="hamburger" @click="sheetOpen = true">☰</button>

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

    <!-- Backdrop -->
    <div v-if="isMobile && sheetOpen" class="backdrop" @click="sheetOpen = false" />

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

    <div class="map-area">
      <GlobeMap
        :sightings="filteredSightings"
        :migrationRoutes="filteredRoutes"
        :selectedSpecies="selectedSpecies"
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
const sheetOpen       = ref(false)

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

/* ── Sheet transition ──────────────────────────────────────── */
.sheet-enter-active, .sheet-leave-active {
  transition: transform 0.32s cubic-bezier(0.32, 0.72, 0, 1);
}
.sheet-enter-from, .sheet-leave-to { transform: translateY(100%); }
</style>
