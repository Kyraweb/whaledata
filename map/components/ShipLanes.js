// Major global shipping corridors as GeoJSON LineStrings
// Sources: IMO traffic separation schemes + major trade route data
export const SHIP_LANES_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    // ── North Atlantic ─────────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'North Atlantic — Europe to North America', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-5, 48], [-15, 47], [-30, 45], [-45, 43], [-55, 42], [-65, 40], [-70, 38]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'North Atlantic — UK to US East Coast', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-2, 51], [-15, 50], [-30, 47], [-45, 44], [-60, 41], [-70, 40], [-74, 40]
      ]}
    },
    // ── South Atlantic ─────────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'South Atlantic — Europe to South America', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [-8, 35], [-15, 25], [-20, 10], [-25, 0], [-30, -15], [-38, -23]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'Cape of Good Hope route', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-8, 35], [-10, 20], [-12, 5], [-10, -10], [-12, -25], [-18, -35], [-20, -38]
      ]}
    },
    // ── Mediterranean / Suez ───────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Mediterranean — Atlantic to Suez', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-5, 36], [5, 37], [15, 37], [25, 34], [32, 31], [33, 28], [35, 25], [38, 20], [43, 13], [48, 12], [50, 13]
      ]}
    },
    // ── Indian Ocean ───────────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Indian Ocean — Suez to Asia', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [50, 13], [55, 12], [60, 10], [65, 8], [72, 8], [78, 8], [80, 7], [82, 8]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'Indian Ocean — Suez to Australia', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [50, 13], [60, 5], [70, -5], [80, -15], [90, -20], [100, -25], [110, -30], [115, -32]
      ]}
    },
    // ── Strait of Malacca / Asia ───────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Strait of Malacca', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [82, 8], [90, 5], [95, 4], [100, 3], [104, 1], [108, 3], [110, 5]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'Asia — China to Japan', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [110, 5], [115, 15], [118, 22], [122, 28], [124, 32], [127, 35], [130, 38]
      ]}
    },
    // ── North Pacific ──────────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'North Pacific — Asia to North America', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [130, 38], [140, 40], [150, 42], [160, 44], [170, 46], [180, 47], [-170, 47], [-160, 46], [-150, 45], [-140, 45], [-130, 46], [-124, 47]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'North Pacific — Asia to US West Coast', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [127, 35], [140, 35], [155, 35], [170, 35], [180, 35], [-170, 34], [-160, 33], [-150, 33], [-140, 33], [-130, 32], [-118, 33]
      ]}
    },
    // ── Panama Canal ───────────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Panama Canal — Pacific approach', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-118, 33], [-110, 25], [-100, 18], [-90, 13], [-82, 9]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'Panama Canal — Atlantic approach', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-80, 9], [-75, 12], [-70, 15], [-65, 18], [-60, 20]
      ]}
    },
    // ── South Pacific ──────────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'South Pacific — Australia to South America', traffic: 'low' },
      geometry: { type: 'LineString', coordinates: [
        [151, -34], [160, -35], [175, -38], [-175, -40], [-160, -38], [-145, -35], [-130, -30], [-118, -28]
      ]}
    },
  ]
}
