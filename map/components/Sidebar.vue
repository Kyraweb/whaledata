<template>
  <aside class="sidebar" :class="{ collapsed }">

    <!-- Header -->
    <div class="sidebar-header">
      <div class="brand">
        <span class="brand-icon">🐋</span>
        <div class="brand-text">
          <div class="brand-title">whaledata<span class="brand-tld">.org</span></div>
          <div class="brand-sub">Global sightings map</div>
        </div>
      </div>
      <button class="collapse-btn" @click="collapsed = !collapsed">
        {{ collapsed ? '›' : '‹' }}
      </button>
    </div>

    <div class="sidebar-body" v-show="!collapsed">

      <!-- Stats bar -->
      <div class="stats-bar">
        <div class="stat">
          <span class="stat-value">{{ totalCount.toLocaleString() }}</span>
          <span class="stat-label">sightings</span>
        </div>
        <div class="stat-divider" />
        <div class="stat">
          <span class="stat-value">{{ speciesList.length }}</span>
          <span class="stat-label">species</span>
        </div>
        <div class="stat-divider" />
        <div class="stat">
          <span class="stat-value">{{ filteredCount.toLocaleString() }}</span>
          <span class="stat-label">shown</span>
        </div>
      </div>

      <!-- Species filter -->
      <div class="filter-section">
        <div class="filter-label">Species</div>
        <div class="species-list">
          <button
            class="species-btn"
            :class="{ active: selectedSpecies === '' }"
            @click="selectSpecies('')"
          >
            <span class="species-dot all-dot" />
            All species
          </button>
          <button
            v-for="s in speciesList"
            :key="s.common_name"
            class="species-btn"
            :class="{ active: selectedSpecies === s.common_name }"
            @click="selectSpecies(s.common_name)"
            :style="{ '--species-color': getSpeciesColor(s.common_name) }"
          >
            <span class="species-dot" :style="{ background: getSpeciesColor(s.common_name) }" />
            <span class="species-name">{{ s.common_name }}</span>
            <span class="species-count">{{ s.sighting_count.toLocaleString() }}</span>
          </button>
        </div>
      </div>

      <!-- Species detail panel -->
      <Transition name="panel">
        <div v-if="activeSpecies" class="species-panel">
          <div class="species-panel-header">
            <div class="species-panel-img-wrap">
              <img
                :src="activeSpecies.photo"
                :alt="activeSpecies.name"
                class="species-panel-img"
                @error="onImgError"
              />
              <div class="species-panel-img-overlay" />
            </div>
            <div class="species-panel-titles">
              <div class="species-panel-name" :style="{ color: getSpeciesColor(activeSpecies.name) }">
                {{ activeSpecies.name }}
              </div>
              <div class="species-panel-sci">{{ activeSpecies.scientific }}</div>
              <div class="species-panel-badges">
                <span class="iucn-badge" :class="activeSpecies.iucn.toLowerCase()">
                  {{ activeSpecies.iucn }}
                </span>
                <span class="iucn-label">{{ activeSpecies.iucnLabel }}</span>
              </div>
            </div>
          </div>

          <div class="species-facts">
            <div v-for="f in activeSpecies.facts" :key="f.label" class="fact">
              <span class="fact-value">{{ f.value }}</span>
              <span class="fact-label">{{ f.label }}</span>
            </div>
          </div>

          <p class="species-desc">{{ activeSpecies.description }}</p>

          <!-- Whale call audio -->
          <div class="audio-section">
            <div class="audio-label">🔊 Whale call</div>
            <audio
              :key="activeSpecies.audio"
              controls
              preload="none"
              class="audio-player"
            >
              <source :src="activeSpecies.audio" :type="activeSpecies.audioType || 'audio/ogg'" />
              Your browser does not support audio.
            </audio>
          </div>
        </div>
      </Transition>

      <!-- Loading state -->
      <div v-if="loading" class="loading-state">
        <div class="loading-dots">
          <span /><span /><span />
        </div>
        <div class="loading-text">Loading sightings…</div>
      </div>

      <!-- Footer -->
      <div class="sidebar-footer">
        <div class="footer-note">Data: GBIF · Updated daily</div>
        <div class="footer-note">
          Hobby project ·
          <a href="https://kyraweb.ca" target="_blank" rel="noopener">kyraweb.ca</a>
        </div>
      </div>

    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  speciesList:     { type: Array,   default: () => [] },
  totalCount:      { type: Number,  default: 0 },
  filteredCount:   { type: Number,  default: 0 },
  selectedSpecies: { type: String,  default: '' },
  loading:         { type: Boolean, default: false }
})

const emit = defineEmits(['species-change'])
const collapsed = ref(false)

const SPECIES_COLORS = {
  'Humpback whale': '#00e5ff',
  'Blue whale':     '#4d9fff',
  'Grey whale':     '#a8c5da',
  'Sperm whale':    '#7eb8d4',
  'Fin whale':      '#5dd4b8',
  'Orca':           '#ff6b9d',
}

// Images via Wikimedia Commons API (allows hotlinking)
// Audio via Wikimedia Commons (ogg format)
const SPECIES_DATA = {
  'Humpback whale': {
    name:        'Humpback whale',
    scientific:  'Megaptera novaeangliae',
    iucn:        'LC',
    iucnLabel:   'Least Concern',
    photo:       'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Humpback_Whale_underwater_shot.jpg/640px-Humpback_Whale_underwater_shot.jpg',
    description: 'Famous for their haunting, complex songs sung only by males. Humpbacks make one of the longest migrations of any mammal, travelling up to 8,000 km between feeding and breeding grounds.',
    facts: [
      { label: 'Length',   value: '14–17m' },
      { label: 'Weight',   value: '25–30t' },
      { label: 'Lifespan', value: '45–100yr' },
    ],
    audio: 'https://upload.wikimedia.org/wikipedia/commons/2/2c/Humpback_Whale_underwater_-_Luc_Rinaldi.ogg'
  },
  'Blue whale': {
    name:        'Blue whale',
    scientific:  'Balaenoptera musculus',
    iucn:        'EN',
    iucnLabel:   'Endangered',
    photo:       'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Blue_whale_size.svg/640px-Blue_whale_size.svg.png',
    description: 'The largest animal ever known to have existed on Earth. A blue whale\'s heart alone weighs as much as a car, and its call can be heard up to 1,600 km away.',
    facts: [
      { label: 'Length',   value: '24–33m' },
      { label: 'Weight',   value: 'up to 200t' },
      { label: 'Lifespan', value: '80–90yr' },
    ],
    audio: 'https://upload.wikimedia.org/wikipedia/commons/5/5d/Blue_Whale_-_NOAA.ogg'
  },
  'Grey whale': {
    name:        'Grey whale',
    scientific:  'Eschrichtius robustus',
    iucn:        'LC',
    iucnLabel:   'Least Concern',
    photo:       'https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/GrayWhale09.jpg/640px-GrayWhale09.jpg',
    description: 'Undertakes the longest migration of any mammal — up to 20,000 km round trip between Arctic feeding grounds and warm Mexican lagoons. The Eastern Pacific population has recovered from near-extinction.',
    facts: [
      { label: 'Length',    value: '13–15m' },
      { label: 'Weight',    value: '15–35t' },
      { label: 'Migration', value: '20,000km' },
    ],
    audio: 'https://upload.wikimedia.org/wikipedia/commons/a/a7/Greywhale.ogg'
  },
  'Sperm whale': {
    name:        'Sperm whale',
    scientific:  'Physeter macrocephalus',
    iucn:        'VU',
    iucnLabel:   'Vulnerable',
    photo:       'https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Sperm_whale_NPS.jpg/640px-Sperm_whale_NPS.jpg',
    description: 'The largest toothed predator on Earth, capable of diving to 3,000m for over 90 minutes. Their clicks are the loudest sounds made by any animal. Immortalised as Moby Dick.',
    facts: [
      { label: 'Length',   value: '15–20m' },
      { label: 'Dive',     value: '3,000m' },
      { label: 'Lifespan', value: '60–70yr' },
    ],
    audio: 'https://upload.wikimedia.org/wikipedia/commons/e/e9/Sperm_Whale_-_NOAA.ogg'
  },
  'Fin whale': {
    name:        'Fin whale',
    scientific:  'Balaenoptera physalus',
    iucn:        'VU',
    iucnLabel:   'Vulnerable',
    photo:       'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Fin_whale_NOAA.jpg/640px-Fin_whale_NOAA.jpg',
    description: 'The second largest animal on Earth, known as the "greyhound of the sea" for its slender build and speed. Their low-frequency songs can travel thousands of kilometres through ocean.',
    facts: [
      { label: 'Length',   value: '18–26m' },
      { label: 'Speed',    value: '37 km/h' },
      { label: 'Lifespan', value: '80–90yr' },
    ],
    audio: 'https://upload.wikimedia.org/wikipedia/commons/d/d7/Fin_Whale_-_NOAA.ogg'
  },
  'Orca': {
    name:        'Orca',
    scientific:  'Orcinus orca',
    iucn:        'DD',
    iucnLabel:   'Data Deficient',
    photo:       'https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Killerwhales_jumping.jpg/640px-Killerwhales_jumping.jpg',
    description: 'The apex predator of the ocean, found in every sea from Arctic to Antarctic. Orcas live in tight family pods with complex social structures and distinct cultural traditions passed between generations.',
    facts: [
      { label: 'Length',   value: '6–8m' },
      { label: 'Weight',   value: '3–6t' },
      { label: 'Lifespan', value: '50–90yr' },
    ],
    audio: 'https://upload.wikimedia.org/wikipedia/commons/7/74/Killerwhale_calls.ogg'
  }
}

const activeSpecies = computed(() => {
  if (!props.selectedSpecies) return null
  return SPECIES_DATA[props.selectedSpecies] || null
})

function getSpeciesColor(name) {
  return SPECIES_COLORS[name] || '#ffffff'
}

function selectSpecies(name) {
  emit('species-change', name)
}

function onImgError(e) {
  e.target.style.display = 'none'
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: 280px;
  background: rgba(8, 13, 26, 0.92);
  backdrop-filter: blur(20px);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width 0.3s ease;
}

.sidebar.collapsed { width: 52px; }

/* Header */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 16px 16px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.brand { display: flex; align-items: center; gap: 10px; overflow: hidden; }
.brand-icon { font-size: 22px; flex-shrink: 0; }
.brand-text { overflow: hidden; white-space: nowrap; }
.brand-title { font-size: 15px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.3px; }
.brand-tld { color: var(--cyan); }
.brand-sub { font-size: 10px; color: var(--text-muted); letter-spacing: 0.08em; text-transform: uppercase; margin-top: 1px; }
.collapse-btn {
  background: none; border: 1px solid var(--border); color: var(--text-secondary);
  width: 24px; height: 24px; border-radius: 6px; cursor: pointer; font-size: 14px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: all 0.2s;
}
.collapse-btn:hover { border-color: var(--border-bright); color: var(--cyan); }

/* Body */
.sidebar-body { flex: 1; overflow-y: auto; display: flex; flex-direction: column; }

/* Stats */
.stats-bar {
  display: flex; align-items: center; padding: 14px 16px;
  border-bottom: 1px solid var(--border); gap: 12px; flex-shrink: 0;
}
.stat { display: flex; flex-direction: column; align-items: center; flex: 1; }
.stat-value { font-size: 16px; font-weight: 700; color: var(--cyan); font-family: var(--font-mono); line-height: 1; }
.stat-label { font-size: 9px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; margin-top: 3px; }
.stat-divider { width: 1px; height: 28px; background: var(--border); }

/* Filter */
.filter-section { padding: 16px; flex-shrink: 0; }
.filter-label { font-size: 9px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 10px; }
.species-list { display: flex; flex-direction: column; gap: 4px; }
.species-btn {
  display: flex; align-items: center; gap: 8px; width: 100%;
  background: none; border: 1px solid transparent; border-radius: 8px;
  padding: 8px 10px; cursor: pointer; color: var(--text-secondary);
  font-family: var(--font-display); font-size: 13px; text-align: left; transition: all 0.15s;
}
.species-btn:hover { background: var(--cyan-glow-soft); border-color: var(--border); color: var(--text-primary); }
.species-btn.active { background: var(--cyan-glow-soft); border-color: var(--border-bright); color: var(--text-primary); }
.species-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.all-dot {
  background: conic-gradient(
    #00e5ff 0deg 60deg, #4d9fff 60deg 120deg, #a8c5da 120deg 180deg,
    #7eb8d4 180deg 240deg, #5dd4b8 240deg 300deg, #ff6b9d 300deg 360deg
  );
}
.species-name { flex: 1; }
.species-count { font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); }

/* ── Species panel ─────────────────────────────────────────── */
.species-panel {
  margin: 0 12px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255,255,255,0.02);
  flex-shrink: 0;
}

.species-panel-header { position: relative; }

.species-panel-img-wrap { position: relative; height: 130px; overflow: hidden; background: #0a1628; }
.species-panel-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.species-panel-img-overlay {
  position: absolute; bottom: 0; left: 0; right: 0; height: 60px;
  background: linear-gradient(to bottom, transparent, rgba(8,13,26,0.95));
}

.species-panel-titles { padding: 10px 12px 8px; }
.species-panel-name { font-size: 14px; font-weight: 700; margin-bottom: 2px; }
.species-panel-sci { font-size: 11px; color: var(--text-muted); font-style: italic; margin-bottom: 8px; }

.species-panel-badges { display: flex; align-items: center; gap: 8px; }
.iucn-badge {
  font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 4px;
  font-family: var(--font-mono); letter-spacing: 0.05em;
}
.iucn-badge.lc  { background: rgba(0,180,100,0.2); color: #00b464; border: 1px solid rgba(0,180,100,0.3); }
.iucn-badge.en  { background: rgba(255,140,0,0.2); color: #ff8c00; border: 1px solid rgba(255,140,0,0.3); }
.iucn-badge.vu  { background: rgba(255,200,0,0.2); color: #ffc800; border: 1px solid rgba(255,200,0,0.3); }
.iucn-badge.dd  { background: rgba(150,150,180,0.2); color: #9696b4; border: 1px solid rgba(150,150,180,0.3); }
.iucn-label { font-size: 11px; color: var(--text-muted); }

.species-facts {
  display: flex; justify-content: space-around;
  padding: 10px 12px; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);
}
.fact { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.fact-value { font-size: 13px; font-weight: 600; color: var(--text-primary); font-family: var(--font-mono); }
.fact-label { font-size: 9px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; }

.species-desc { font-size: 11px; color: var(--text-secondary); line-height: 1.7; padding: 10px 12px; margin: 0; }

.audio-section { padding: 8px 12px 12px; }
.audio-label { font-size: 10px; color: var(--text-muted); margin-bottom: 6px; }
.audio-player { width: 100%; height: 32px; filter: invert(1) hue-rotate(180deg) brightness(0.8); }

/* Panel transition */
.panel-enter-active, .panel-leave-active { transition: all 0.25s ease; }
.panel-enter-from, .panel-leave-to { opacity: 0; transform: translateY(-8px); max-height: 0; }
.panel-enter-to, .panel-leave-from { opacity: 1; transform: translateY(0); max-height: 600px; }

/* Loading */
.loading-state { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 32px 16px; }
.loading-dots { display: flex; gap: 6px; }
.loading-dots span {
  width: 6px; height: 6px; border-radius: 50%; background: var(--cyan);
  animation: pulse 1.2s ease-in-out infinite;
}
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes pulse {
  0%, 100% { opacity: 0.2; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1); }
}
.loading-text { font-size: 12px; color: var(--text-muted); }

/* Footer */
.sidebar-footer { padding: 14px 16px; border-top: 1px solid var(--border); margin-top: auto; flex-shrink: 0; }
.footer-note { font-size: 10px; color: var(--text-muted); line-height: 1.8; }
.footer-note a { color: var(--cyan-dim); text-decoration: none; }
.footer-note a:hover { color: var(--cyan); }
</style>
