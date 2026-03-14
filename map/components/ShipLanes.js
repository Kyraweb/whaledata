// Major global shipping lanes based on actual trade routes
export const SHIP_LANES_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    // ── Transatlantic ──────────────────────────────────────────
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
    // ── Europe to South America ────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Europe to Brazil', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [-9, 39], [-15, 30], [-20, 15], [-25, 0], [-32, -10], [-38, -23]
      ]}
    },
    // ── Europe/Asia via Cape of Good Hope ──────────────────────
    {
      type: 'Feature',
      properties: { name: 'Cape of Good Hope — Europe to Asia', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-9, 39], [-13, 28], [-15, 15], [-12, 0], [-8, -15], [-10, -28], [-16, -35], [-18, -38], [-15, -42],
        [10, -40], [30, -38], [45, -35], [55, -25], [60, -18], [65, -10], [70, 0], [72, 8]
      ]}
    },
    // ── Suez Canal route ───────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Suez Canal — Europe to Indian Ocean', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [4, 52], [5, 45], [8, 38], [12, 35], [18, 33], [25, 32], [32, 30], [33, 27],
        [37, 22], [42, 15], [44, 12], [48, 12], [52, 13], [58, 14], [63, 16]
      ]}
    },
    // ── Indian Ocean — Suez to Asia ────────────────────────────
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
    // ── Strait of Malacca to East Asia ────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Malacca to South China Sea', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [104, 1], [106, 4], [109, 8], [112, 14], [114, 18], [116, 22], [121, 25], [122, 31], [121, 37]
      ]}
    },
    // ── North Pacific — Asia to North America ──────────────────
    {
      type: 'Feature',
      properties: { name: 'North Pacific — Japan to US West Coast', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [136, 35], [145, 38], [155, 40], [165, 43], [175, 45], [-175, 46],
        [-165, 47], [-155, 47], [-145, 46], [-135, 47], [-125, 47], [-122, 47]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'North Pacific — China to US West Coast', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [121, 31], [130, 33], [140, 35], [152, 36], [163, 37], [173, 37],
        [-177, 36], [-165, 35], [-152, 34], [-140, 34], [-130, 33], [-118, 34]
      ]}
    },
    // ── Panama Canal connections ───────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'US West Coast to Panama Canal', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-118, 34], [-115, 28], [-107, 20], [-95, 14], [-82, 9]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'Panama Canal to US East Coast', traffic: 'high' },
      geometry: { type: 'LineString', coordinates: [
        [-80, 9], [-77, 14], [-73, 20], [-70, 25], [-68, 30], [-72, 35], [-74, 40]
      ]}
    },
    // ── South Atlantic ─────────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'South Atlantic — Brazil to Europe', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [-43, -23], [-35, -15], [-28, -5], [-22, 5], [-18, 15], [-14, 25], [-10, 36], [-9, 39]
      ]}
    },
    // ── Australia routes ───────────────────────────────────────
    {
      type: 'Feature',
      properties: { name: 'Australia to East Asia', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [151, -34], [153, -28], [152, -20], [148, -15], [138, -10], [130, -5], [118, 2], [112, 5], [108, 4], [104, 1]
      ]}
    },
    {
      type: 'Feature',
      properties: { name: 'Australia to Europe via Cape', traffic: 'medium' },
      geometry: { type: 'LineString', coordinates: [
        [115, -32], [100, -35], [80, -38], [55, -38], [35, -36], [20, -35], [15, -32],
        [18, -38], [16, -42], [10, -40]
      ]}
    },
  ]
}
