// Shared organ constants (spec §6.3) -- independent of how the body is rendered.

export const ORGAN_LABELS = {
  brain: 'Brain', heart: 'Heart', lungs: 'Lungs', liver: 'Liver', stomach: 'Stomach',
  intestines: 'Intestines', kidneys: 'Kidneys', pancreas: 'Pancreas',
  blood_vessels: 'Blood vessels', muscle: 'Muscle', skin: 'Skin', fat: 'Fat',
  thyroid: 'Thyroid', spleen: 'Spleen', bladder: 'Bladder',
}

// Hex, not rgba -- both CSS (legend swatches) and three.js (THREE.Color) need plain hex.
export const LEVEL_COLORS = { high: '#22d3ee', medium: '#1594a8', low: '#0d5964' }
export const LEVEL_OPACITY = { high: 0.95, medium: 0.7, low: 0.45 }
export const HIGHLIGHT_COLOR = '#ff9d5c'
export const GHOST_COLOR = '#5b7a8a' // organs with no body_map entry: faint, no data
