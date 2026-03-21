// ============================================================
// ConservationLayers.js
// Feeding grounds and naval sonar exercise zones
// Sources: NOAA, IWC, scientific literature
// ============================================================

// ── Feeding Grounds ───────────────────────────────────────────
export const FEEDING_GROUNDS = {
  type: 'FeatureCollection',
  features: [

    // Humpback whale
    {
      type: 'Feature',
      properties: { name: 'Gulf of Maine', species: 'Humpback whale', color: '#00e5ff', type: 'feeding' },
      geometry: { type: 'Polygon', coordinates: [[
        [-71, 41], [-65, 41], [-65, 45], [-71, 45], [-71, 41]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'Gulf of Alaska', species: 'Humpback whale', color: '#00e5ff', type: 'feeding' },
      geometry: { type: 'Polygon', coordinates: [[
        [-155, 56], [-145, 56], [-145, 61], [-155, 61], [-155, 56]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'Antarctic Peninsula Feeding', species: 'Humpback whale', color: '#00e5ff', type: 'feeding' },
      geometry: { type: 'Polygon', coordinates: [[
        [-70, -65], [-55, -65], [-55, -60], [-70, -60], [-70, -65]
      ]]}
    },

    // Blue whale
    {
      type: 'Feature',
      properties: { name: 'Sea of Cortez', species: 'Blue whale', color: '#4d9fff', type: 'feeding' },
      geometry: { type: 'Polygon', coordinates: [[
        [-115, 23], [-108, 23], [-108, 30], [-115, 30], [-115, 23]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'California Upwelling Zone', species: 'Blue whale', color: '#4d9fff', type: 'feeding' },
      geometry: { type: 'Polygon', coordinates: [[
        [-125, 34], [-118, 34], [-118, 40], [-125, 40], [-125, 34]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'Sri Lanka Feeding Ground', species: 'Blue whale', color: '#4d9fff', type: 'feeding' },
      geometry: { type: 'Polygon', coordinates: [[
        [78, 4], [85, 4], [85, 10], [78, 10], [78, 4]
      ]]}
    },

    // Grey whale
    {
      type: 'Feature',
      properties: { name: 'Bering Sea Feeding', species: 'Grey whale', color: '#a8c5da', type: 'feeding' },
      geometry: { type: 'Polygon', coordinates: [[
        [-180, 55], [-160, 55], [-160, 65], [-180, 65], [-180, 55]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'Chukchi Sea', species: 'Grey whale', color: '#a8c5da', type: 'feeding' },
      geometry: { type: 'Polygon', coordinates: [[
        [-175, 65], [-155, 65], [-155, 72], [-175, 72], [-175, 65]
      ]]}
    },

    // Sperm whale
    {
      type: 'Feature',
      properties: { name: 'Azores Feeding Ground', species: 'Sperm whale', color: '#7eb8d4', type: 'feeding' },
      geometry: { type: 'Polygon', coordinates: [[
        [-30, 36], [-22, 36], [-22, 42], [-30, 42], [-30, 36]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'Galapagos Feeding Zone', species: 'Sperm whale', color: '#7eb8d4', type: 'feeding' },
      geometry: { type: 'Polygon', coordinates: [[
        [-95, -5], [-85, -5], [-85, 5], [-95, 5], [-95, -5]
      ]]}
    },

    // Fin whale
    {
      type: 'Feature',
      properties: { name: 'Ligurian Sea', species: 'Fin whale', color: '#5dd4b8', type: 'feeding' },
      geometry: { type: 'Polygon', coordinates: [[
        [4, 42], [10, 42], [10, 45], [4, 45], [4, 42]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'Gulf of St Lawrence', species: 'Fin whale', color: '#5dd4b8', type: 'feeding' },
      geometry: { type: 'Polygon', coordinates: [[
        [-66, 47], [-58, 47], [-58, 51], [-66, 51], [-66, 47]
      ]]}
    },

    // Orca
    {
      type: 'Feature',
      properties: { name: 'Salish Sea', species: 'Orca', color: '#ff6b9d', type: 'feeding' },
      geometry: { type: 'Polygon', coordinates: [[
        [-125, 47], [-121, 47], [-121, 50], [-125, 50], [-125, 47]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'Norwegian Orca Grounds', species: 'Orca', color: '#ff6b9d', type: 'feeding' },
      geometry: { type: 'Polygon', coordinates: [[
        [14, 68], [22, 68], [22, 72], [14, 72], [14, 68]
      ]]}
    },
  ]
}

// ── Sonar / Naval Exercise Zones ──────────────────────────────
export const SONAR_ZONES = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { name: 'SOCAL Range Complex', authority: 'US Navy', risk: 'high' },
      geometry: { type: 'Polygon', coordinates: [[
        [-122, 30], [-115, 30], [-115, 34], [-122, 34], [-122, 30]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'Hawaii Range Complex', authority: 'US Navy', risk: 'high' },
      geometry: { type: 'Polygon', coordinates: [[
        [-162, 18], [-154, 18], [-154, 24], [-162, 24], [-162, 18]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'Atlantic Fleet Training Area', authority: 'US Navy', risk: 'high' },
      geometry: { type: 'Polygon', coordinates: [[
        [-78, 28], [-68, 28], [-68, 36], [-78, 36], [-78, 28]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'AUTEC Bahamas', authority: 'US Navy', risk: 'high' },
      geometry: { type: 'Polygon', coordinates: [[
        [-78, 23], [-73, 23], [-73, 27], [-78, 27], [-78, 23]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'ALOHA Cabled Observatory', authority: 'US Navy', risk: 'medium' },
      geometry: { type: 'Polygon', coordinates: [[
        [-160, 22], [-156, 22], [-156, 24], [-160, 24], [-160, 22]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'Mediterranean NATO Exercise Zone', authority: 'NATO', risk: 'high' },
      geometry: { type: 'Polygon', coordinates: [[
        [0, 36], [10, 36], [10, 42], [0, 42], [0, 36]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'North Sea Exercise Area', authority: 'NATO', risk: 'medium' },
      geometry: { type: 'Polygon', coordinates: [[
        [0, 56], [8, 56], [8, 60], [0, 60], [0, 56]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'Japan Maritime Self-Defense', authority: 'JMSDF', risk: 'medium' },
      geometry: { type: 'Polygon', coordinates: [[
        [130, 30], [138, 30], [138, 36], [130, 36], [130, 30]
      ]]}
    },
    {
      type: 'Feature',
      properties: { name: 'Australian Defence Exercise Area', authority: 'ADF', risk: 'medium' },
      geometry: { type: 'Polygon', coordinates: [[
        [113, -32], [120, -32], [120, -27], [113, -27], [113, -32]
      ]]}
    },
  ]
}
