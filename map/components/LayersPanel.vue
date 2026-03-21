<template>
  <!-- Data Layers button -->
  <button class="map-btn btn-data" :class="{ active: open }" @click="open = !open; conservationOpen = false">
    <span>⚡</span>
    <span>Data Layers</span>
    <span v-if="activeCount > 1" class="map-btn-badge">{{ activeCount }}</span>
  </button>

  <!-- Conservation button -->
  <button class="map-btn btn-conservation" :class="{ active: conservationOpen }" @click="conservationOpen = !conservationOpen; open = false">
    <span>🌿</span>
    <span>Conservation</span>
    <span v-if="activeConservationCount > 0" class="map-btn-badge conservation-badge">{{ activeConservationCount }}</span>
  </button>

  <!-- Data Layers Panel -->
  <Transition name="layers-panel">
    <div v-if="open" class="layers-panel layers-panel-data">
      <div class="lp-header">
        <span class="lp-title">Data Layers</span>
        <button class="lp-close" @click="open = false">✕</button>
      </div>

      <div class="lp-body">
        <div
          v-for="layer in LAYERS"
          :key="layer.key"
          class="lp-layer"
          :class="{ active: modelValue[layer.key] }"
        >
          <div class="lp-layer-header" @click="toggle(layer.key)">
            <div class="lp-dot" :style="{ background: layer.color, boxShadow: `0 0 6px ${layer.color}` }"></div>
            <div class="lp-layer-info">
              <div class="lp-layer-name">{{ layer.label }}</div>
              <div class="lp-layer-source">{{ layer.source }}</div>
            </div>
            <div class="lp-count" :style="{ color: layer.color }">
              {{ layerTotal(layer.key).toLocaleString() }}
            </div>
            <div class="lp-switch" :class="{ on: modelValue[layer.key] }">
              <div class="lp-switch-thumb"></div>
            </div>
          </div>

          <!-- Per-species breakdown when layer is active and species is selected -->
          <div v-if="modelValue[layer.key] && selectedSpecies && speciesCount(layer.key, selectedSpecies) > 0" class="lp-species-count">
            <span :style="{ color: speciesColor(selectedSpecies) }">{{ selectedSpecies }}</span>
            <span class="lp-species-n">{{ speciesCount(layer.key, selectedSpecies).toLocaleString() }} records</span>
          </div>
          <div v-else-if="modelValue[layer.key] && selectedSpecies && speciesCount(layer.key, selectedSpecies) === 0" class="lp-species-count lp-none">
            No {{ selectedSpecies.toLowerCase() }} records in this layer
          </div>
        </div>
      </div>

      <div class="lp-footer">
        <button class="lp-all" @click="setAll(true)">All on</button>
        <button class="lp-all" @click="setAll(false)">All off</button>
      </div>
    </div>
  </Transition>

  <!-- Conservation Panel -->
  <Transition name="layers-panel">
    <div v-if="conservationOpen" class="layers-panel layers-panel-conservation">
      <div class="lp-header">
        <span class="lp-title">Conservation Layers</span>
        <button class="lp-close" @click="conservationOpen = false">✕</button>
      </div>
      <div class="lp-body">
        <div
          v-for="layer in CONSERVATION"
          :key="layer.key"
          class="lp-layer"
          :class="{ active: conservationValue[layer.key] }"
        >
          <div class="lp-layer-header" @click="toggleConservation(layer.key)">
            <div class="lp-dot" :style="{ background: layer.color, boxShadow: `0 0 6px ${layer.color}`, borderRadius: '3px' }"></div>
            <div class="lp-layer-info">
              <div class="lp-layer-name">{{ layer.label }}</div>
              <div class="lp-layer-source">{{ layer.desc }}</div>
            </div>
            <div class="lp-switch" :class="{ on: conservationValue[layer.key] }">
              <div class="lp-switch-thumb"></div>
            </div>
          </div>
        </div>
      </div>
      <div class="lp-footer">
        <button class="lp-all" @click="toggleConservation('feeding'); toggleConservation('sonar')">All on</button>
        <button class="lp-all" @click="emit('update:conservationValue', { feeding: false, sonar: false })">All off</button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue:        { type: Object, required: true },
  conservationValue: { type: Object, required: true },
  layersSummary:     { type: Object, default: () => ({}) },
  selectedSpecies:   { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'update:conservationValue'])

const open             = ref(false)
const conservationOpen = ref(false)

const CONSERVATION = [
  { key: 'feeding', label: 'Feeding Grounds',  desc: 'Known foraging areas per species', color: '#00c97a' },
  { key: 'sonar',   label: 'Sonar Exercise Zones', desc: 'Naval sonar exercise areas — risk to cetaceans', color: '#ff4444' },
]

const LAYERS = [
  { key: 'sightings',   label: 'Sightings',   source: 'GBIF · OBIS',     color: '#00e5ff' },
  { key: 'strandings',  label: 'Strandings',  source: 'NOAA · OBIS',     color: '#ff5a5a' },
  { key: 'acoustics',   label: 'Acoustics',   source: 'NOAA PACM · OBIS',color: '#9664ff' },
  { key: 'inaturalist', label: 'iNaturalist', source: 'iNaturalist.org',  color: '#64c864' },
  { key: 'historical',  label: 'Historical',  source: 'GBIF pre-1950',    color: '#ffb432' },
]

const SPECIES_COLORS = {
  'Humpback whale': '#00e5ff', 'Blue whale': '#4d9fff',
  'Grey whale': '#a8c5da',     'Sperm whale': '#7eb8d4',
  'Fin whale': '#5dd4b8',      'Orca': '#ff6b9d',
}
function speciesColor(name) { return SPECIES_COLORS[name] || '#fff' }

const activeCount             = computed(() => Object.values(props.modelValue).filter(Boolean).length)
const activeConservationCount = computed(() => Object.values(props.conservationValue).filter(Boolean).length)

function layerTotal(key) {
  return props.layersSummary[key]?.total || 0
}

function speciesCount(layerKey, species) {
  const data = props.layersSummary[layerKey]?.data || []
  const row  = data.find(r => r.common_name === species)
  return row?.count || 0
}

function toggle(key) {
  emit('update:modelValue', { ...props.modelValue, [key]: !props.modelValue[key] })
}

function toggleConservation(key) {
  emit('update:conservationValue', { ...props.conservationValue, [key]: !props.conservationValue[key] })
}

function setAll(val) {
  const next = {}
  LAYERS.forEach(l => next[l.key] = val)
  // Always keep sightings on
  emit('update:modelValue', next)
}
</script>

<style scoped>
/* ── Map buttons (shared base) ─────────────────────────────── */
.map-btn {
  position: fixed;
  bottom: 32px;
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
  z-index: 200;
  transition: all 0.2s;
  white-space: nowrap;
}

/* Data Layers — cyan */
.btn-data {
  left: 320px;
  border: 1px solid rgba(0, 229, 255, 0.25);
  color: rgba(0, 229, 255, 0.7);
}
.btn-data:hover, .btn-data.active {
  background: rgba(0, 229, 255, 0.1);
  border-color: rgba(0, 229, 255, 0.5);
  color: #00e5ff;
  box-shadow: 0 0 16px rgba(0, 229, 255, 0.15);
}

/* Conservation — green */
.btn-conservation {
  left: 480px;
  border: 1px solid rgba(0, 201, 122, 0.25);
  color: rgba(0, 201, 122, 0.7);
}
.btn-conservation:hover, .btn-conservation.active {
  background: rgba(0, 201, 122, 0.1);
  border-color: rgba(0, 201, 122, 0.5);
  color: #00c97a;
  box-shadow: 0 0 16px rgba(0, 201, 122, 0.15);
}

.map-btn-badge {
  background: #00e5ff;
  color: #050810;
  font-size: 10px;
  font-weight: 700;
  border-radius: 10px;
  padding: 1px 6px;
}
.conservation-badge { background: #00c97a; }

/* ── Panels ────────────────────────────────────────────────── */
.layers-panel {
  position: fixed;
  bottom: 80px;
  width: 280px;
  background: rgba(8, 13, 26, 0.97);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(0, 229, 255, 0.2);
  border-radius: 16px;
  z-index: 200;
  box-shadow: 0 0 40px rgba(0, 229, 255, 0.06);
  overflow: hidden;
}

.layers-panel-data        { left: 320px; }
.layers-panel-conservation { left: 480px; }

.lp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px 10px;
  border-bottom: 1px solid var(--border);
}
.lp-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
}
.lp-close {
  width: 24px; height: 24px;
  background: none;
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}

.lp-body { padding: 8px; }

/* ── Layer row ─────────────────────────────────────────────── */
.lp-layer {
  border-radius: 10px;
  margin-bottom: 4px;
  overflow: hidden;
  border: 1px solid transparent;
  transition: border-color 0.15s;
}
.lp-layer.active { border-color: var(--border); }

.lp-layer-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 10px;
  cursor: pointer;
  border-radius: 10px;
  transition: background 0.15s;
}
.lp-layer-header:hover { background: rgba(255,255,255,0.03); }

.lp-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.lp-layer-info { flex: 1; min-width: 0; }
.lp-layer-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.2;
}
.lp-layer-source {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 1px;
}

.lp-count {
  font-size: 11px;
  font-family: var(--font-mono);
  font-weight: 600;
  flex-shrink: 0;
}

/* Toggle switch */
.lp-switch {
  width: 32px; height: 18px;
  border-radius: 9px;
  background: var(--border);
  flex-shrink: 0;
  position: relative;
  transition: background 0.2s;
}
.lp-switch.on { background: var(--cyan); }
.lp-switch-thumb {
  position: absolute;
  top: 2px; left: 2px;
  width: 14px; height: 14px;
  border-radius: 50%;
  background: #050810;
  transition: transform 0.2s;
}
.lp-switch.on .lp-switch-thumb { transform: translateX(14px); }

/* Species count line */
.lp-species-count {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px 8px;
  font-size: 11px;
  border-top: 1px solid var(--border);
}
.lp-species-n { font-family: var(--font-mono); color: var(--text-muted); }
.lp-none { color: var(--text-muted); font-size: 11px; }

/* Footer */
.lp-footer {
  display: flex;
  gap: 8px;
  padding: 8px;
  border-top: 1px solid var(--border);
}
.lp-all {
  flex: 1;
  padding: 6px;
  background: none;
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-muted);
  font-family: var(--font-display);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
}
.lp-all:hover { border-color: var(--border-bright); color: var(--text-primary); }

/* Transition */
.layers-panel-enter-active, .layers-panel-leave-active { transition: all 0.2s ease; }
.layers-panel-enter-from, .layers-panel-leave-to { opacity: 0; transform: translateY(8px); }

@media (max-width: 767px) {
  .btn-data         { left: 12px;  bottom: 76px; font-size: 12px; padding: 8px 14px; }
  .btn-conservation { left: 150px; bottom: 76px; font-size: 12px; padding: 8px 14px; }
  .layers-panel-data, .layers-panel-conservation { left: 12px; right: 12px; width: auto; bottom: 130px; }
}
</style>
