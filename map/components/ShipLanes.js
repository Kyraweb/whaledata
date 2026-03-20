// Major global shipping corridors
export const SHIP_LANES_GEOJSON = {
  type: 'FeatureCollection',
  features: [

    // ── North Atlantic ─────────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'North Atlantic — Northern Europe to US East Coast', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [4, 52], [-2, 51], [-8, 50], [-20, 49], [-35, 47], [-50, 44], [-60, 42], [-70, 40], [-74, 40]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'North Atlantic — Southern Europe to US East Coast', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-9, 39], [-18, 36], [-30, 34], [-45, 33], [-58, 32], [-68, 32], [-74, 38]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'North Atlantic — Canada to UK', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [-63, 44], [-50, 46], [-35, 48], [-20, 50], [-8, 51], [0, 52]
      ]}
    },

    // ── South Atlantic ─────────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'South Atlantic — Europe to Brazil', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [-9, 39], [-15, 30], [-20, 15], [-25, 0], [-32, -10], [-38, -23]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'South Atlantic — Brazil to Europe', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [-43, -23], [-35, -15], [-28, -5], [-22, 5], [-18, 15], [-14, 25], [-10, 36], [-9, 39]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'South Atlantic — Brazil to South Africa', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [-43, -23], [-38, -28], [-30, -32], [-20, -34], [-10, -34], [0, -33], [10, -33], [18, -33]
      ]}
    },

    // ── Cape of Good Hope ──────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Cape of Good Hope — Europe to Asia', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-9, 39], [-13, 28], [-15, 15], [-12, 0], [-8, -15], [-10, -28],
        [-16, -35], [-18, -38], [-15, -42], [0, -40], [20, -38], [35, -36],
        [45, -35], [55, -25], [60, -18], [65, -10], [70, 0], [72, 8]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'Cape of Good Hope — Asia to Americas', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [18, -33], [15, -38], [10, -42], [0, -42], [-15, -40], [-28, -35], [-38, -28], [-43, -23]
      ]}
    },

    // ── Mediterranean & Suez ───────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Mediterranean — Atlantic to Suez Canal', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-5, 36], [0, 37], [8, 38], [15, 37], [22, 35], [28, 33], [32, 31],
        [33, 28], [37, 22], [42, 15], [44, 12], [48, 12], [52, 13], [56, 22], [58, 24]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'Black Sea to Mediterranean', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [30, 43], [29, 41], [27, 38], [24, 37], [20, 37], [15, 37]
      ]}
    },

    // ── Indian Ocean ───────────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Indian Ocean — Gulf to India', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [56, 24], [60, 22], [62, 18], [65, 12], [68, 8], [72, 8], [77, 8]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'Indian Ocean — India to Malacca', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [77, 8], [82, 7], [88, 5], [95, 4], [100, 3], [104, 1]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'Indian Ocean — East Africa to India', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [40, -10], [48, -5], [55, 2], [60, 8], [65, 12], [70, 15], [72, 18]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'Indian Ocean — Australia to Middle East', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [115, -32], [105, -28], [90, -20], [75, -10], [65, 0], [58, 12], [52, 18], [48, 22]
      ]}
    },

    // ── Strait of Malacca & South China Sea ───────────────────
    {
      type: 'Feature',
      properties: { name: 'Strait of Malacca', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [100, 3], [102, 2], [104, 1], [106, 2], [108, 4], [110, 6]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'South China Sea — Singapore to Japan', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [104, 1], [108, 5], [112, 10], [114, 16], [116, 20], [118, 24], [121, 28], [122, 31], [121, 37]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'South China Sea — Singapore to Hong Kong', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [104, 1], [108, 8], [112, 15], [114, 22]
      ]}
    },

    // ── North Pacific ──────────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'North Pacific — Japan to US West Coast (west)', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [136, 35], [145, 38], [155, 40], [165, 43], [175, 45], [180, 46]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'North Pacific — Japan to US West Coast (east)', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-180, 46], [-170, 47], [-160, 47], [-150, 47], [-140, 46], [-130, 46], [-122, 47]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'North Pacific — China to US West Coast (west)', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [121, 31], [130, 33], [140, 35], [152, 36], [163, 37], [173, 37], [180, 37]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'North Pacific — China to US West Coast (east)', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-180, 37], [-170, 36], [-158, 35], [-145, 34], [-132, 33], [-118, 34]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'North Pacific — Korea/Japan to Canada', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [129, 35], [138, 38], [148, 42], [160, 46], [172, 48], [180, 48], [-172, 48], [-158, 48], [-140, 49], [-128, 49], [-123, 49]
      ]}
    },

    // ── Panama Canal ───────────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Panama Canal — Pacific to Caribbean', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-118, 34], [-110, 25], [-100, 18], [-90, 13], [-82, 9], [-80, 9], [-77, 14],
        [-73, 20], [-70, 25], [-68, 30], [-72, 35], [-74, 40]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'Gulf of Mexico — US ports', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-90, 29], [-88, 28], [-85, 26], [-82, 24], [-80, 25], [-80, 28]
      ]}
    },

    // ── South Pacific ──────────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'South Pacific — Australia to Panama (west)', traffic: 'low' },
      geometry: { type: 'LineString', coordinates: [
        [151, -34], [160, -35], [175, -38], [180, -40]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'South Pacific — Australia to Panama (east)', traffic: 'low' },
      geometry: { type: 'LineString', coordinates: [
        [-180, -40], [-160, -38], [-145, -35], [-130, -30], [-118, -28]
      ]}
    },

    // ── Australia routes ───────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Australia — East Coast to Asia', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [151, -34], [154, -26], [156, -18], [155, -12], [152, -8],
        [148, -5], [140, -2], [130, 0], [120, 2], [112, 4], [108, 4], [104, 1]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'Australia — West Coast to Middle East', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [115, -32], [105, -28], [90, -20], [75, -10], [65, 0], [58, 12], [52, 18]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'Australia — East to West Coast', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [151, -34], [148, -40], [140, -44], [128, -44], [118, -40], [115, -35]
      ]}
    },

    // ── Arctic / Northern routes ───────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Northern Sea Route — Europe to Asia', traffic: 'low' },
      geometry: { type: 'LineString', coordinates: [
        [30, 70], [50, 72], [70, 74], [90, 75], [110, 74], [130, 72], [150, 70], [165, 65]
      ]}
    },

    // ── Africa routes ──────────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'West Africa — Europe to Gulf of Guinea', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [-9, 39], [-12, 30], [-15, 20], [-16, 10], [-14, 5], [-8, 3], [2, 3], [5, 5]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'East Africa — Suez to Mozambique', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [44, 12], [46, 8], [48, 4], [46, -2], [44, -8], [42, -14], [38, -20], [36, -26], [34, -30]
      ]}
    },

    // ── Caribbean & Central America ────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Caribbean — US East Coast to Venezuela', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [-74, 38], [-72, 34], [-70, 28], [-68, 22], [-65, 16], [-63, 12], [-62, 10], [-65, 10]
      ]}
    },

    // ── Trans-Indian Ocean ─────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Indian Ocean — South Africa to Australia', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [18, -33], [30, -36], [45, -38], [60, -36], [75, -32], [90, -28], [105, -28], [115, -32]
      ]}
    },
  ]
}
