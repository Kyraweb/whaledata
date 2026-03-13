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

      <!-- Loading state -->
      <div v-if="loading" class="loading-state">
        <div class="loading-dots">
          <span /><span /><span />
        </div>
        <div class="loading-text">Loading sightings…</div>
      </div>

      <!-- Footer -->
      <div class="sidebar-footer">
        <div class="footer-note">
          Data: GBIF · Updated daily
        </div>
        <div class="footer-note">
          Hobby project ·
          <a href="https://kyraweb.ca" target="_blank" rel="noopener">kyraweb.ca</a>
        </div>
      </div>

    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  speciesList:     { type: Array,  default: () => [] },
  totalCount:      { type: Number, default: 0 },
  filteredCount:   { type: Number, default: 0 },
  selectedSpecies: { type: String, default: '' },
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

function getSpeciesColor(name) {
  return SPECIES_COLORS[name] || '#ffffff'
}

function selectSpecies(name) {
  emit('species-change', name)
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

.sidebar.collapsed {
  width: 52px;
}

/* Header */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 16px 16px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
}

.brand-icon {
  font-size: 22px;
  flex-shrink: 0;
}

.brand-text {
  overflow: hidden;
  white-space: nowrap;
}

.brand-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

.brand-tld {
  color: var(--cyan);
}

.brand-sub {
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-top: 1px;
}

.collapse-btn {
  background: none;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  width: 24px;
  height: 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.collapse-btn:hover {
  border-color: var(--border-bright);
  color: var(--cyan);
}

/* Body */
.sidebar-body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* Stats */
.stats-bar {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  gap: 12px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: var(--cyan);
  font-family: var(--font-mono);
  line-height: 1;
}

.stat-label {
  font-size: 9px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-top: 3px;
}

.stat-divider {
  width: 1px;
  height: 28px;
  background: var(--border);
}

/* Filter */
.filter-section {
  padding: 16px;
  flex: 1;
}

.filter-label {
  font-size: 9px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-bottom: 10px;
}

.species-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.species-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  background: none;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 8px 10px;
  cursor: pointer;
  color: var(--text-secondary);
  font-family: var(--font-display);
  font-size: 13px;
  text-align: left;
  transition: all 0.15s;
}

.species-btn:hover {
  background: var(--cyan-glow-soft);
  border-color: var(--border);
  color: var(--text-primary);
}

.species-btn.active {
  background: var(--cyan-glow-soft);
  border-color: var(--border-bright);
  color: var(--text-primary);
}

.species-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.all-dot {
  background: conic-gradient(
    #00e5ff 0deg 60deg,
    #4d9fff 60deg 120deg,
    #a8c5da 120deg 180deg,
    #7eb8d4 180deg 240deg,
    #5dd4b8 240deg 300deg,
    #ff6b9d 300deg 360deg
  );
}

.species-name {
  flex: 1;
}

.species-count {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 32px 16px;
}

.loading-dots {
  display: flex;
  gap: 6px;
}

.loading-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--cyan);
  animation: pulse 1.2s ease-in-out infinite;
}

.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes pulse {
  0%, 100% { opacity: 0.2; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1); }
}

.loading-text {
  font-size: 12px;
  color: var(--text-muted);
}

/* Footer */
.sidebar-footer {
  padding: 14px 16px;
  border-top: 1px solid var(--border);
  margin-top: auto;
}

.footer-note {
  font-size: 10px;
  color: var(--text-muted);
  line-height: 1.8;
}

.footer-note a {
  color: var(--cyan-dim);
  text-decoration: none;
}

.footer-note a:hover {
  color: var(--cyan);
}
</style>
