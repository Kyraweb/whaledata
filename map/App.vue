<template>
  <div class="app">
    <Sidebar
      :speciesList="speciesSummary"
      :totalCount="totalCount"
      :filteredCount="filteredSightings.length"
      :selectedSpecies="selectedSpecies"
      :loading="loading"
      :isMobile="isMobile"
      :sheetOpen="sheetOpen"
      @species-change="onSpeciesChange"
      @sheet-close="sheetOpen = false"
    />

    <!-- Mobile bottom bar -->
    <div v-if="isMobile" class="mobile-bar" @click="sheetOpen = true">
      <div class="mobile-bar-stats">
        <span class="mobile-stat">
          <span class="mobile-stat-value">{{ totalCount.toLocaleString() }}</span>
          <span class="mobile-stat-label">sightings</span>
        </span>
        <span class="mobile-stat-divider" />
        <span class="mobile-stat">
          <span class="mobile-stat-value">{{ speciesSummary.length }}</span>
          <span class="mobile-stat-label">species</span>
        </span>
      </div>
      <div class="mobile-bar-cta">
        <span>{{ selectedSpecies || 'All species' }}</span>
        <span class="mobile-bar-arrow">▲</span>
      </div>
    </div>

    <!-- Sheet backdrop -->
    <Transition name="backdrop">
      <div v-if="isMobile && sheetOpen" class="sheet-backdrop" @click="sheetOpen = false" />
    </Transition>

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

const allSightings      = ref([])
const allRoutes         = ref([])
const speciesSummary    = ref([])
const selectedSpecies   = ref('')
const loading           = ref(true)
const isMobile          = ref(false)
const sheetOpen         = ref(false)

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

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
  if (isMobile.value) sheetOpen.value = false
}

async function loadData() {
  loading.value = true
  try {
    const [sightingsRes, summaryRes, routesRes] = await Promise.all([
      fetch(`${API_URL}/sightings/?limit=5000`),
      fetch(`${API_URL}/sightings/species-summary`),
      fetch(`${API_URL}/routes/`)
    ])
    const sightingsData = await sightingsRes.json()
    const summaryData   = await summaryRes.json()
    const routesData    = await routesRes.json()
    allSightings.value   = sightingsData.data || []
    speciesSummary.value = summaryData.data   || []
    allRoutes.value      = routesData.data    || []
  } catch (err) {
    console.error('Failed to load whale data:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  loadData()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.app {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  position: relative;
}

.map-area {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
}

/* ── Mobile bottom bar ─────────────────────────────────────── */
.mobile-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: rgba(8, 13, 26, 0.95);
  backdrop-filter: blur(20px);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  z-index: 150;
  cursor: pointer;
}

.mobile-bar-stats {
  display: flex;
  align-items: center;
  gap: 14px;
}

.mobile-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.mobile-stat-value {
  font-size: 15px;
  font-weight: 700;
  color: var(--cyan);
  font-family: var(--font-mono);
  line-height: 1;
}

.mobile-stat-label {
  font-size: 9px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-top: 2px;
}

.mobile-stat-divider {
  width: 1px;
  height: 24px;
  background: var(--border);
}

.mobile-bar-cta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

.mobile-bar-arrow {
  color: var(--cyan);
  font-size: 10px;
}

/* ── Sheet backdrop ────────────────────────────────────────── */
.sheet-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 199;
}

.backdrop-enter-active, .backdrop-leave-active { transition: opacity 0.25s ease; }
.backdrop-enter-from, .backdrop-leave-to { opacity: 0; }
</style>
