<template>
  <div id="app" :class="{ mobile: isMobile }">

    <!-- ── Desktop sidebar ── -->
    <Sidebar
      v-if="!isMobile"
      :species="species"
      :selected-species="selectedSpecies"
      :sighting-count="filteredCount"
      :loading="loading"
      @select-species="selectSpecies"
    />

    <!-- ── Map ── -->
    <div class="map-area" :class="{ 'map-area-desktop': !isMobile }">
      <GlobeMap
        ref="globeMap"
        :sightings="filteredSightings"
        :routes="routes"
        :selected-species="selectedSpecies"
        :is-mobile="isMobile"
        :year-range="yearRange"
        :active-layers="activeLayers"
        @map-ready="onMapReady"
      />
    </div>

    <!-- ── Layers panel ── -->
    <LayersPanel
      v-if="showLayersPanel"
      :active-layers="activeLayers"
      :active-sources="activeSources"
      :initial-tab="layersPanelTab"
      @update-layers="activeLayers = $event"
      @update-sources="activeSources = $event"
      @close="showLayersPanel = false"
    />

    <!-- ── Date filter panel ── -->
    <div v-if="showDateFilter" class="date-filter-panel">
      <div class="date-filter-header">
        <span class="date-filter-title">Year Range</span>
        <button class="date-filter-close" @click="showDateFilter = false">✕</button>
      </div>
      <div class="year-display">{{ yearRange[0] }} – {{ yearRange[1] }}</div>
      <div class="slider-row">
        <input type="range" :min="1800" :max="2025" v-model.number="yearRange[0]"
          @input="clampYears" class="year-slider" />
        <input type="range" :min="1800" :max="2025" v-model.number="yearRange[1]"
          @input="clampYears" class="year-slider" />
      </div>
      <div class="year-labels"><span>1800</span><span>2025</span></div>
    </div>

    <!-- ── 4-slot bottom bar ── -->
    <div v-if="!isMobile" class="bottom-bar">
      <button
        class="bar-btn"
        :class="{ active: showLayersPanel && layersPanelTab === 'data' }"
        @click="openLayersTab('data')"
      >
        <span class="bar-btn-icon">⊞</span>
        <span class="bar-btn-label">Data Layers</span>
      </button>
      <button
        class="bar-btn"
        :class="{ active: showLayersPanel && layersPanelTab === 'conservation' }"
        @click="openLayersTab('conservation')"
      >
        <span class="bar-btn-icon">🐋</span>
        <span class="bar-btn-label">Conservation</span>
      </button>
      <button
        class="bar-btn"
        :class="{ active: shipLanesActive }"
        @click="toggleShipLanes"
      >
        <span class="bar-btn-icon">🚢</span>
        <span class="bar-btn-label">Ship Lanes</span>
      </button>
      <button
        class="bar-btn"
        :class="{ active: showDateFilter }"
        @click="showDateFilter = !showDateFilter"
      >
        <span class="bar-btn-icon">📅</span>
        <span class="bar-btn-label">Date Filter</span>
        <span v-if="yearFiltered" class="bar-btn-badge">●</span>
      </button>
    </div>

    <!-- ── Top-right controls ── -->
    <div class="top-right-controls">
      <button class="ctrl-btn" @click="nearMe" title="Near me (N)">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/>
          <line x1="12" y1="2" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="22"/>
          <line x1="2" y1="12" x2="5" y2="12"/><line x1="19" y1="12" x2="22" y2="12"/>
        </svg>
        <span>Near me</span>
      </button>
      <button class="ctrl-btn" @click="showAlertsModal = true" title="Email alerts">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </svg>
        <span>Alerts</span>
      </button>
      <button class="ctrl-btn" @click="showContactModal = true" title="Contact">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
          <polyline points="22,6 12,13 2,6"/>
        </svg>
        <span>Contact</span>
      </button>
      <button class="ctrl-btn" @click="showOnboarding = true" title="Help">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <span>Help</span>
      </button>
      <button class="ctrl-btn share-btn" @click="shareUrl" title="Share (S)">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/>
          <circle cx="18" cy="19" r="3"/>
          <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
          <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
        </svg>
        <span v-if="shareCopied">Copied!</span>
        <span v-else>Share</span>
      </button>
    </div>

    <!-- ── Onboarding overlay ── -->
    <Transition name="onboard">
      <div v-if="showOnboarding" class="onboarding-overlay" @click.self="dismissOnboarding">
        <div class="onboarding-card">
          <div class="onboarding-logo">🐋 whaledata.org</div>
          <h2 class="onboarding-title">Explore 25,000+ whale sightings</h2>
          <p class="onboarding-sub">Here's what's on the map and how to navigate it.</p>

          <div class="onboarding-grid">
            <div class="onboarding-item">
              <div class="onboarding-icon" style="background:rgba(0,229,255,0.1);color:#00e5ff">⊞</div>
              <div class="onboarding-text">
                <strong>Data Layers</strong>
                <span>Toggle sighting sources — GBIF, OBIS, iNaturalist, strandings, acoustics, historical</span>
              </div>
            </div>
            <div class="onboarding-item">
              <div class="onboarding-icon" style="background:rgba(0,201,122,0.1);color:#00c97a">🐋</div>
              <div class="onboarding-text">
                <strong>Conservation</strong>
                <span>Show whale feeding grounds and naval sonar exercise zones</span>
              </div>
            </div>
            <div class="onboarding-item">
              <div class="onboarding-icon" style="background:rgba(255,159,67,0.1);color:#ff9f43">🚢</div>
              <div class="onboarding-text">
                <strong>Ship Lanes</strong>
                <span>Overlay global shipping corridors to see vessel-whale conflict zones</span>
              </div>
            </div>
            <div class="onboarding-item">
              <div class="onboarding-icon" style="background:rgba(150,100,255,0.1);color:#9664ff">📅</div>
              <div class="onboarding-text">
                <strong>Date Filter</strong>
                <span>Filter sightings by year range — from historical records to today</span>
              </div>
            </div>
            <div class="onboarding-item">
              <div class="onboarding-icon" style="background:rgba(0,229,255,0.08);color:#00b8cc">◎</div>
              <div class="onboarding-text">
                <strong>Near me</strong>
                <span>Find whale sightings near your current location</span>
              </div>
            </div>
            <div class="onboarding-item">
              <div class="onboarding-icon" style="background:rgba(0,229,255,0.08);color:#7a9bb5">⌨</div>
              <div class="onboarding-text">
                <strong>Keyboard shortcuts</strong>
                <span>Keys 1–6 filter by species · 0 shows all · Space pauses rotation · Esc closes panels</span>
              </div>
            </div>
          </div>

          <button class="onboarding-cta" @click="dismissOnboarding">
            Got it, explore →
          </button>

          <div class="onboarding-hint">You can reopen this guide anytime with the Help button</div>
        </div>
      </div>
    </Transition>

    <!-- ── Contact modal ── -->
    <Transition name="modal-fade">
      <div v-if="showContactModal" class="modal-backdrop" @click.self="showContactModal = false">
        <div class="modal-card">
          <div class="modal-header">
            <h3>Get in touch</h3>
            <button class="modal-close" @click="showContactModal = false">✕</button>
          </div>
          <form @submit.prevent="submitContact">
            <div class="form-group">
              <label>Name</label>
              <input v-model="contactForm.name" type="text" placeholder="Your name" required />
            </div>
            <div class="form-group">
              <label>Email</label>
              <input v-model="contactForm.email" type="email" placeholder="you@example.com" required />
            </div>
            <div class="form-group">
              <label>Message</label>
              <textarea v-model="contactForm.message" rows="4" placeholder="Report an issue, ask a question, or just say hello..." required></textarea>
            </div>
            <button type="submit" class="form-submit" :disabled="contactSubmitting">
              {{ contactSubmitting ? 'Sending…' : 'Send message' }}
            </button>
            <div v-if="contactSent" class="form-success">✓ Message sent — thank you!</div>
          </form>
        </div>
      </div>
    </Transition>

    <!-- ── Alerts modal ── -->
    <Transition name="modal-fade">
      <div v-if="showAlertsModal" class="modal-backdrop" @click.self="showAlertsModal = false">
        <div class="modal-card">
          <div class="modal-header">
            <h3>Weekly sighting alerts</h3>
            <button class="modal-close" @click="showAlertsModal = false">✕</button>
          </div>
          <p class="modal-intro">Get a weekly digest of new whale sightings delivered to your inbox.</p>
          <form @submit.prevent="submitAlerts">
            <div class="form-group">
              <label>Email address</label>
              <input v-model="alertsEmail" type="email" placeholder="you@example.com" required />
            </div>
            <button type="submit" class="form-submit" :disabled="alertsSubmitting">
              {{ alertsSubmitting ? 'Subscribing…' : 'Subscribe' }}
            </button>
            <div v-if="alertsSent" class="form-success">✓ Check your inbox to confirm!</div>
          </form>
        </div>
      </div>
    </Transition>

    <!-- ── Mobile: hamburger ── -->
    <button v-if="isMobile && !sheetOpen" class="mobile-hamburger" @click="sheetOpen = true">
      <span></span><span></span><span></span>
    </button>

    <!-- ── Mobile: species info btn ── -->
    <button v-if="isMobile && selectedSpecies && !sheetOpen" class="mobile-info-btn" @click="sheetDetailOpen = true">
      ⓘ
    </button>

    <!-- ── Mobile: stats bar ── -->
    <div v-if="isMobile" class="mobile-stats-bar">
      <div class="mobile-stat">
        <span class="mobile-stat-num">{{ filteredCount.toLocaleString() }}</span>
        <span class="mobile-stat-lbl">sightings</span>
      </div>
      <div class="mobile-stat">
        <span class="mobile-stat-num">{{ species.length }}</span>
        <span class="mobile-stat-lbl">species</span>
      </div>
      <div class="mobile-stat">
        <span class="mobile-stat-species">{{ selectedSpecies || 'All species' }}</span>
      </div>
    </div>

    <!-- ── Mobile: backdrop ── -->
    <div v-if="isMobile && (sheetOpen || sheetDetailOpen)" class="mobile-backdrop"
      @click="sheetOpen = false; sheetDetailOpen = false"></div>

    <!-- ── Mobile: filter sheet ── -->
    <Transition name="sheet">
      <div v-if="isMobile && sheetOpen" class="mobile-sheet">
        <div class="sheet-handle"></div>
        <div class="sheet-header">
          <span>Filter species</span>
          <button class="sheet-close" @click="sheetOpen = false">✕</button>
        </div>
        <div class="sheet-species-list">
          <button class="sheet-species-item" :class="{ active: !selectedSpecies }" @click="selectSpecies(null); sheetOpen = false">
            All species
            <span class="sheet-species-count">{{ sightings.length.toLocaleString() }}</span>
          </button>
          <button v-for="s in species" :key="s.id" class="sheet-species-item"
            :class="{ active: selectedSpecies === s.name }"
            @click="selectSpecies(s.name); sheetOpen = false">
            <span class="sheet-species-dot" :style="{ background: getSpeciesColor(s.name) }"></span>
            {{ s.name }}
            <span class="sheet-species-count">{{ s.sighting_count?.toLocaleString() }}</span>
          </button>
        </div>
      </div>
    </Transition>

    <!-- ── Mobile: species detail sheet ── -->
    <Transition name="sheet">
      <div v-if="isMobile && sheetDetailOpen && selectedSpeciesData" class="mobile-sheet mobile-sheet-detail">
        <div class="sheet-handle"></div>
        <div class="sheet-header">
          <span>{{ selectedSpeciesData.name }}</span>
          <button class="sheet-close" @click="sheetDetailOpen = false">✕</button>
        </div>
        <div class="sheet-detail-body">
          <img v-if="selectedSpeciesData.photo_url" :src="selectedSpeciesData.photo_url"
            :alt="selectedSpeciesData.name" class="sheet-detail-img" />
          <div class="sheet-iucn" :class="`iucn-${selectedSpeciesData.iucn_status}`">
            {{ selectedSpeciesData.iucn_status }}
          </div>
          <p class="sheet-detail-desc">{{ selectedSpeciesData.description }}</p>
        </div>
      </div>
    </Transition>

    <!-- ── Share toast ── -->
    <Transition name="toast">
      <div v-if="shareCopied" class="share-toast">Link copied to clipboard</div>
    </Transition>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import GlobeMap from './components/GlobeMap.vue'
import Sidebar from './components/Sidebar.vue'
import LayersPanel from './components/LayersPanel.vue'

const API = import.meta.env.VITE_API_URL || 'https://api.whaledata.org'

// ─── State ────────────────────────────────────────────────────────────────────

const globeMap = ref(null)
const sightings = ref([])
const species = ref([])
const routes = ref([])
const loading = ref(true)

const selectedSpecies = ref(null)
const yearRange = ref([1900, 2025])

// All sources ON by default (sprint item 1)
const activeSources = ref({
  gbif: true,
  obis: true,
  inaturalist: true,
  strandings: true,
  acoustics: true,
  historical: true,
})

const activeLayers = ref({
  feedingGrounds: false,
  sonarZones: false,
})

// Panel visibility
const showLayersPanel = ref(false)
const layersPanelTab = ref('data')
const showDateFilter = ref(false)
const shipLanesActive = computed(() => globeMap.value?.shipLanesActive ?? false)

// Mobile
const isMobile = ref(window.innerWidth < 768)
const sheetOpen = ref(false)
const sheetDetailOpen = ref(false)

// Modals
const showContactModal = ref(false)
const showAlertsModal = ref(false)
const contactForm = ref({ name: '', email: '', message: '' })
const contactSubmitting = ref(false)
const contactSent = ref(false)
const alertsEmail = ref('')
const alertsSubmitting = ref(false)
const alertsSent = ref(false)

// Share
const shareCopied = ref(false)

// Onboarding (sprint item 2)
const ONBOARDING_KEY = 'wd_onboarding_done'
const showOnboarding = ref(!localStorage.getItem(ONBOARDING_KEY))

// ─── Computed ─────────────────────────────────────────────────────────────────

const filteredSightings = computed(() => {
  let s = sightings.value

  // Filter by active sources
  s = s.filter(x => activeSources.value[x.source] !== false)

  // Land filter
  s = s.filter(x => !isLandlocked(x.longitude, x.latitude))

  return s
})

const filteredCount = computed(() => filteredSightings.value.length)

const yearFiltered = computed(() => yearRange.value[0] !== 1900 || yearRange.value[1] !== 2025)

const selectedSpeciesData = computed(() =>
  species.value.find(s => s.name === selectedSpecies.value) ?? null
)

// ─── Land filter ──────────────────────────────────────────────────────────────

function isLandlocked(lng, lat) {
  if (lng === null || lat === null) return true
  // Paraguay / Bolivia interior
  if (lng > -64 && lng < -55 && lat > -28 && lat < -15) return true
  // Himalayas / Central Asia
  if (lng > 65 && lng < 100 && lat > 28 && lat < 50) return true
  // Sahara interior
  if (lng > -5 && lng < 40 && lat > 15 && lat < 30) return true
  // Amazon interior
  if (lng > -72 && lng < -48 && lat > -15 && lat < 0) return true
  return false
}

// ─── Data fetching ────────────────────────────────────────────────────────────

async function fetchAll() {
  try {
    const [sRes, spRes, rRes] = await Promise.all([
      fetch(`${API}/sightings/?limit=25000`),
      fetch(`${API}/species`),
      fetch(`${API}/routes/`),
    ])
    sightings.value = await sRes.json()
    species.value = await spRes.json()
    routes.value = await rRes.json()
  } catch (e) {
    console.error('Fetch error:', e)
  } finally {
    loading.value = false
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getSpeciesColor(name) {
  const map = {
    'humpback': '#00e5ff',
    'blue':     '#00b8cc',
    'grey':     '#00c97a',
    'orca':     '#9664ff',
    'sperm':    '#ffb432',
    'fin':      '#ff6b9d',
  }
  const lower = name?.toLowerCase() ?? ''
  for (const [k, v] of Object.entries(map)) {
    if (lower.includes(k)) return v
  }
  return '#00e5ff'
}

function clampYears() {
  if (yearRange.value[0] > yearRange.value[1]) {
    yearRange.value[0] = yearRange.value[1]
  }
}

// ─── Bottom bar actions (sprint item 3) ───────────────────────────────────────

function openLayersTab(tab) {
  if (showLayersPanel.value && layersPanelTab.value === tab) {
    showLayersPanel.value = false
  } else {
    layersPanelTab.value = tab
    showLayersPanel.value = true
    showDateFilter.value = false
  }
}

function toggleShipLanes() {
  globeMap.value?.toggleShipLanes()
}

// ─── Species selection ────────────────────────────────────────────────────────

function selectSpecies(name) {
  selectedSpecies.value = name
  // Restore rotation if deselecting
}

// ─── Near me ─────────────────────────────────────────────────────────────────

function nearMe() {
  if (!navigator.geolocation) return
  navigator.geolocation.getCurrentPosition(pos => {
    globeMap.value?.flyTo(pos.coords.longitude, pos.coords.latitude, 6)
  })
}

// ─── Share ────────────────────────────────────────────────────────────────────

function shareUrl() {
  const params = new URLSearchParams()
  if (selectedSpecies.value) params.set('species', selectedSpecies.value)
  if (yearRange.value[0] !== 1900) params.set('from', yearRange.value[0])
  if (yearRange.value[1] !== 2025) params.set('to', yearRange.value[1])
  const url = `${location.origin}${params.toString() ? '?' + params : ''}`
  navigator.clipboard.writeText(url).then(() => {
    shareCopied.value = true
    setTimeout(() => { shareCopied.value = false }, 2500)
  })
}

function loadStateFromUrl() {
  const params = new URLSearchParams(location.search)
  if (params.get('species')) selectedSpecies.value = params.get('species')
  if (params.get('from')) yearRange.value[0] = parseInt(params.get('from'))
  if (params.get('to')) yearRange.value[1] = parseInt(params.get('to'))
}

// ─── Contact / alerts ─────────────────────────────────────────────────────────

async function submitContact() {
  contactSubmitting.value = true
  try {
    await fetch(`${API}/alerts/contact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(contactForm.value),
    })
    contactSent.value = true
    contactForm.value = { name: '', email: '', message: '' }
    setTimeout(() => { showContactModal.value = false; contactSent.value = false }, 2500)
  } catch (e) {
    console.error(e)
  } finally {
    contactSubmitting.value = false
  }
}

async function submitAlerts() {
  alertsSubmitting.value = true
  try {
    await fetch(`${API}/alerts/subscribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: alertsEmail.value }),
    })
    alertsSent.value = true
    setTimeout(() => { showAlertsModal.value = false; alertsSent.value = false }, 2500)
  } catch (e) {
    console.error(e)
  } finally {
    alertsSubmitting.value = false
  }
}

// ─── Onboarding ───────────────────────────────────────────────────────────────

function dismissOnboarding() {
  showOnboarding.value = false
  localStorage.setItem(ONBOARDING_KEY, '1')
}

// ─── Keyboard shortcuts ───────────────────────────────────────────────────────

function onKeyDown(e) {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
  const speciesNames = species.value.map(s => s.name)
  switch (e.key) {
    case '1': case '2': case '3': case '4': case '5': case '6': {
      const idx = parseInt(e.key) - 1
      if (speciesNames[idx]) selectedSpecies.value = speciesNames[idx]
      break
    }
    case '0': selectedSpecies.value = null; break
    case 'Escape':
      showLayersPanel.value = false
      showDateFilter.value = false
      showContactModal.value = false
      showAlertsModal.value = false
      showOnboarding.value = false
      sheetOpen.value = false
      break
    case 'n': case 'N': nearMe(); break
    case 's': case 'S': shareUrl(); break
  }
}

// ─── Resize ───────────────────────────────────────────────────────────────────

function onResize() {
  isMobile.value = window.innerWidth < 768
}

// ─── Map ready ────────────────────────────────────────────────────────────────

function onMapReady() {
  // nothing needed — data already bound via props
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────

onMounted(() => {
  fetchAll()
  loadStateFromUrl()
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('resize', onResize)
})
</script>

<style>
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --cyan: #00e5ff;
  --cyan-dim: #00b8cc;
  --dark: #050810;
  --surface: #0a1525;
  --surface2: #0d1e32;
  --border: rgba(0,229,255,0.1);
  --border2: rgba(0,229,255,0.2);
  --text: #e8f4f8;
  --text2: #7a9bb5;
  --text3: #3a5a72;
  --green: #00c97a;
  --amber: #ffb432;
  --purple: #9664ff;
  --orange: #ff9f43;
}

html, body { width: 100%; height: 100%; overflow: hidden; background: var(--dark); }

#app {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
  font-family: 'DM Sans', sans-serif;
  color: var(--text);
}

/* ── Map area ── */
.map-area { position: absolute; inset: 0; }
.map-area-desktop { left: 300px; }
.mobile .map-area { left: 0; }

/* ── 4-slot bottom bar (sprint item 3) ── */
.bottom-bar {
  position: absolute;
  bottom: 20px;
  left: calc(300px + 20px);
  right: 20px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  background: rgba(5, 8, 16, 0.88);
  border: 1px solid var(--border);
  border-radius: 14px;
  backdrop-filter: blur(16px);
  overflow: hidden;
  z-index: 20;
}

.bar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  background: transparent;
  border: none;
  border-right: 1px solid var(--border);
  color: var(--text2);
  font-size: 13px;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  transition: all 0.18s;
  position: relative;
}
.bar-btn:last-child { border-right: none; }
.bar-btn:hover { background: rgba(0,229,255,0.05); color: var(--text); }
.bar-btn.active {
  background: rgba(0,229,255,0.08);
  color: var(--cyan);
}
.bar-btn-icon { font-size: 15px; line-height: 1; }
.bar-btn-label { font-size: 12px; font-weight: 500; }
.bar-btn-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 8px;
  color: var(--cyan);
  line-height: 1;
}

/* ── Top-right controls ── */
.top-right-controls {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  gap: 8px;
  z-index: 20;
}

.ctrl-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(5,8,16,0.88);
  border: 1px solid var(--border);
  border-radius: 40px;
  color: var(--text2);
  font-size: 12px;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  transition: all 0.15s;
  backdrop-filter: blur(12px);
  white-space: nowrap;
}
.ctrl-btn:hover { border-color: var(--border2); color: var(--text); }
.ctrl-btn svg { flex-shrink: 0; }

/* ── Date filter panel ── */
.date-filter-panel {
  position: absolute;
  bottom: 80px;
  right: 20px;
  width: 280px;
  background: rgba(10, 21, 37, 0.96);
  border: 1px solid var(--border2);
  border-radius: 14px;
  padding: 18px 20px;
  z-index: 25;
  backdrop-filter: blur(16px);
}
.date-filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.date-filter-title {
  font-family: 'Syne', sans-serif;
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
}
.date-filter-close {
  background: none;
  border: none;
  color: var(--text3);
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  line-height: 1;
}
.year-display {
  font-family: 'DM Mono', monospace;
  font-size: 20px;
  font-weight: 500;
  color: var(--cyan);
  text-align: center;
  margin-bottom: 14px;
}
.slider-row { display: flex; flex-direction: column; gap: 8px; }
.year-slider {
  width: 100%;
  accent-color: var(--cyan);
  cursor: pointer;
}
.year-labels {
  display: flex;
  justify-content: space-between;
  font-family: 'DM Mono', monospace;
  font-size: 10px;
  color: var(--text3);
  margin-top: 4px;
}

/* ── Onboarding overlay (sprint item 2) ── */
.onboarding-overlay {
  position: fixed;
  inset: 0;
  background: rgba(5, 8, 16, 0.82);
  backdrop-filter: blur(6px);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.onboarding-card {
  background: rgba(10, 21, 37, 0.98);
  border: 1px solid var(--border2);
  border-radius: 20px;
  padding: 40px 44px;
  max-width: 640px;
  width: 100%;
  backdrop-filter: blur(24px);
  box-shadow: 0 32px 80px rgba(0,0,0,0.6), 0 0 60px rgba(0,229,255,0.04);
}
.onboarding-logo {
  font-family: 'Syne', sans-serif;
  font-size: 14px;
  font-weight: 700;
  color: var(--cyan);
  margin-bottom: 16px;
  letter-spacing: 0.02em;
}
.onboarding-title {
  font-family: 'Syne', sans-serif;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: 8px;
  color: var(--text);
}
.onboarding-sub {
  font-size: 15px;
  color: var(--text2);
  margin-bottom: 28px;
  font-weight: 300;
}
.onboarding-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 28px;
}
.onboarding-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px;
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--border);
  border-radius: 12px;
}
.onboarding-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}
.onboarding-text {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.onboarding-text strong {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}
.onboarding-text span {
  font-size: 12px;
  color: var(--text2);
  line-height: 1.5;
  font-weight: 300;
}
.onboarding-cta {
  width: 100%;
  padding: 14px;
  background: var(--cyan);
  color: var(--dark);
  border: none;
  border-radius: 40px;
  font-family: 'Syne', sans-serif;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.18s;
  margin-bottom: 14px;
}
.onboarding-cta:hover {
  background: #fff;
  box-shadow: 0 8px 32px rgba(0,229,255,0.3);
  transform: translateY(-1px);
}
.onboarding-hint {
  text-align: center;
  font-size: 12px;
  color: var(--text3);
}

/* Onboarding animation */
.onboard-enter-active, .onboard-leave-active { transition: opacity 0.3s, transform 0.3s; }
.onboard-enter-from, .onboard-leave-to { opacity: 0; transform: scale(0.97); }

/* ── Modals ── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(5,8,16,0.7);
  backdrop-filter: blur(4px);
  z-index: 150;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal-card {
  background: rgba(10, 21, 37, 0.98);
  border: 1px solid var(--border2);
  border-radius: 16px;
  padding: 28px 32px;
  width: 100%;
  max-width: 420px;
  backdrop-filter: blur(20px);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.modal-header h3 {
  font-family: 'Syne', sans-serif;
  font-size: 18px;
  font-weight: 700;
}
.modal-close {
  background: none;
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text2);
  width: 32px;
  height: 32px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s;
}
.modal-close:hover { border-color: var(--border2); color: var(--text); }
.modal-intro { font-size: 14px; color: var(--text2); margin-bottom: 20px; line-height: 1.6; font-weight: 300; }

.form-group { margin-bottom: 16px; }
.form-group label {
  display: block;
  font-size: 11px;
  font-family: 'DM Mono', monospace;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text3);
  margin-bottom: 6px;
}
.form-group input, .form-group textarea {
  width: 100%;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  color: var(--text);
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s;
  resize: vertical;
}
.form-group input:focus, .form-group textarea:focus { border-color: var(--border2); }
.form-submit {
  width: 100%;
  padding: 12px;
  background: var(--cyan);
  color: var(--dark);
  border: none;
  border-radius: 40px;
  font-family: 'Syne', sans-serif;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s;
}
.form-submit:hover:not(:disabled) { background: #fff; }
.form-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.form-success { text-align: center; color: var(--green); font-size: 13px; margin-top: 12px; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.2s; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }

/* ── Share toast ── */
.share-toast {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(10,21,37,0.96);
  border: 1px solid var(--border2);
  border-radius: 40px;
  padding: 10px 22px;
  font-size: 13px;
  color: var(--cyan);
  z-index: 100;
  pointer-events: none;
  backdrop-filter: blur(12px);
}
.toast-enter-active, .toast-leave-active { transition: opacity 0.2s, transform 0.2s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }

/* ── Mobile controls ── */
.mobile-hamburger {
  position: fixed;
  top: 18px;
  left: 18px;
  z-index: 60;
  width: 44px;
  height: 44px;
  background: rgba(5,8,16,0.88);
  border: 1px solid var(--border);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  backdrop-filter: blur(12px);
}
.mobile-hamburger span {
  display: block;
  width: 20px;
  height: 2px;
  background: var(--cyan);
  border-radius: 2px;
}

.mobile-info-btn {
  position: fixed;
  top: 18px;
  left: 72px;
  z-index: 60;
  width: 44px;
  height: 44px;
  background: rgba(5,8,16,0.88);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--cyan);
  font-size: 18px;
  cursor: pointer;
  backdrop-filter: blur(12px);
}

.mobile-stats-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 50;
  background: rgba(5,8,16,0.92);
  border-top: 1px solid var(--border);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  backdrop-filter: blur(12px);
}
.mobile-stat { display: flex; flex-direction: column; gap: 1px; }
.mobile-stat-num {
  font-family: 'Syne', sans-serif;
  font-size: 16px;
  font-weight: 700;
  color: var(--cyan);
  line-height: 1;
}
.mobile-stat-lbl { font-size: 10px; color: var(--text3); font-family: 'DM Mono', monospace; letter-spacing: 0.1em; }
.mobile-stat-species { font-size: 13px; color: var(--text2); font-weight: 500; }

/* ── Mobile sheet ── */
.mobile-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 299;
}
.mobile-sheet {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 300;
  background: rgba(10,21,37,0.98);
  border-top: 1px solid var(--border);
  border-radius: 20px 20px 0 0;
  padding: 0 0 40px;
  max-height: 85vh;
  overflow-y: auto;
  backdrop-filter: blur(20px);
}
.sheet-handle {
  width: 40px;
  height: 4px;
  background: var(--border2);
  border-radius: 4px;
  margin: 12px auto 0;
}
.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  font-family: 'Syne', sans-serif;
  font-size: 15px;
  font-weight: 700;
  border-bottom: 1px solid var(--border);
}
.sheet-close {
  background: none;
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text2);
  width: 30px;
  height: 30px;
  cursor: pointer;
  font-size: 13px;
}
.sheet-species-list { padding: 8px 0; }
.sheet-species-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 14px 20px;
  background: transparent;
  border: none;
  color: var(--text2);
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s;
  text-align: left;
}
.sheet-species-item:hover, .sheet-species-item.active {
  background: rgba(0,229,255,0.06);
  color: var(--text);
}
.sheet-species-item.active { color: var(--cyan); }
.sheet-species-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.sheet-species-count { margin-left: auto; font-family: 'DM Mono', monospace; font-size: 12px; color: var(--text3); }

.sheet-detail-body { padding: 16px 20px; }
.sheet-detail-img { width: 100%; height: 200px; object-fit: cover; border-radius: 12px; margin-bottom: 14px; }
.sheet-iucn {
  display: inline-block;
  font-family: 'DM Mono', monospace;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 20px;
  margin-bottom: 12px;
  font-weight: 500;
}
.iucn-EN, .iucn-VU { background: rgba(255,164,0,0.12); color: #ffb432; }
.iucn-LC           { background: rgba(0,201,122,0.12); color: #00c97a; }
.sheet-detail-desc { font-size: 14px; color: var(--text2); line-height: 1.7; font-weight: 300; }

.sheet-enter-active, .sheet-leave-active { transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.sheet-enter-from, .sheet-leave-to { transform: translateY(100%); }

/* ── Responsive ── */
@media (max-width: 767px) {
  .bottom-bar, .top-right-controls { display: none; }
}
@media (max-width: 900px) {
  .bar-btn-label { font-size: 11px; }
  .ctrl-btn span { display: none; }
  .ctrl-btn { padding: 8px 10px; }
}
</style>
