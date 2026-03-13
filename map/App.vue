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

    <div class="map-area" :style="{ marginLeft: sidebarWidth }">
      <GlobeMap
        :sightings="filteredSightings"
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

const allSightings    = ref([])
const speciesSummary  = ref([])
const selectedSpecies = ref('')
const loading         = ref(true)
const sidebarWidth    = ref('280px')

const totalCount = computed(() =>
  speciesSummary.value.reduce((sum, s) => sum + s.sighting_count, 0)
)

const filteredSightings = computed(() => {
  if (!selectedSpecies.value) return allSightings.value
  return allSightings.value.filter(s => s.common_name === selectedSpecies.value)
})

function onSpeciesChange(species) {
  selectedSpecies.value = species
}

async function loadData() {
  loading.value = true
  try {
    const [sightingsRes, summaryRes] = await Promise.all([
      fetch(`${API_URL}/sightings/?limit=5000`),
      fetch(`${API_URL}/sightings/species-summary`)
    ])

    const sightingsData = await sightingsRes.json()
    const summaryData   = await summaryRes.json()

    allSightings.value   = sightingsData.data || []
    speciesSummary.value = summaryData.data || []
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
  transition: margin-left 0.3s ease;
}
</style>
