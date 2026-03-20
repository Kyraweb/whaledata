<template>
  <div class="app">
    <!-- Hamburger — mobile only -->
    <button v-if="isMobile" class="hamburger" @click="sheetOpen = !sheetOpen">
      <span v-if="!sheetOpen">☰</span>
      <span v-else>✕</span>
    </button>

    <!-- Sidebar / bottom sheet -->
    <Transition name="sheet">
      <Sidebar
        v-if="!isMobile || sheetOpen"
        :speciesList="speciesSummary"
        :totalCount="totalCount"
        :filteredCount="filteredSightings.length"
        :selectedSpecies="selectedSpecies"
        :loading="loading"
        :isMobile="isMobile"
        @species-change="onSpeciesChange"
        @close="sheetOpen = false"
      />
    </Transition>

    <!-- Backdrop — tap outside to close, behind sheet -->
    <div
      v-if="isMobile && sheetOpen"
      class="backdrop"
      @click="sheetOpen = false"
    />

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

function checkMobile() {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) sheetOpen.value = false
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
    allSightings.value   = (await sightingsRes.json()).data || []
    speciesSummary.value = (await summaryRes.json()).data   || []
    allRoutes.value      = (await routesRes.json()).data    || []
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
onUnmounted(() => window.removeEventListener('resize', checkMobile))
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
  inset: 0;
}

/* Hamburger button */
.hamburger {
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 400;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(8, 13, 26, 0.92);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border-bright);
  color: var(--cyan);
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.hamburger:hover {
  background: var(--cyan-glow);
}

/* Backdrop — z-index BELOW sheet (300) */
.backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  z-index: 299;
}

/* Sheet transition */
.sheet-enter-active,
.sheet-leave-active {
  transition: transform 0.32s cubic-bezier(0.32, 0.72, 0, 1);
}
.sheet-enter-from,
.sheet-leave-to {
  transform: translateY(100%);
}
</style>
