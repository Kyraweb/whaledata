<template>
  <div class="app">
    <Sidebar
      :speciesList="speciesSummary"
      :totalCount="totalCount"
      :filteredCount="filteredSightings.length"
      :selectedSpecies="selectedSpecies"
      :loading="loading"
      @species-change="onSpeciesChange"
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
import { ref, computed, onMounted } from 'vue'
import GlobeMap from './components/GlobeMap.vue'
import Sidebar from './components/Sidebar.vue'

const API_URL = import.meta.env.VITE_API_URL || 'https://api.whaledata.org'

const allSightings      = ref([])
const allRoutes         = ref([])
const speciesSummary    = ref([])
const selectedSpecies   = ref('')
const loading           = ref(true)

const totalCount = computed(() => allSightings.value.filter(isOceanSighting).length)

function isOceanSighting(s) {
  const lng = parseFloat(s.longitude)
  const lat = parseFloat(s.latitude)
  // Filter clearly landlocked regions only — avoid blocking coastal/ocean areas
  // Amazon basin / inland South America (not the coast)
  if (lng > -72 && lng < -44 && lat > -18 && lat < 8) return false
  // Himalayan region — Nepal, Bhutan, far inland India
  if (lng > 70 && lng < 100 && lat > 22 && lat < 38) return false
  // Central Asia — Kazakhstan, Mongolia etc
  if (lng > 50 && lng < 120 && lat > 38 && lat < 58) return false
  // Sahara / sub-Saharan inland Africa
  if (lng > 10 && lng < 40 && lat > 5 && lat < 22) return false
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
  loadData()
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
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
</style>
