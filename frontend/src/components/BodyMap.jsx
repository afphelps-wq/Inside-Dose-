import { useId } from 'react'

// Placeholder illustrated body, restyled as a dark-HUD wireframe scan (see
// UI examples/). Each of the 15 organs (spec §6.3) is a separate element
// whose id is its organ key, so a real CC-licensed scan SVG can drop in later.

export const LEVEL_COLORS = {
  high: 'rgba(34, 211, 238, 0.95)',
  medium: 'rgba(34, 211, 238, 0.55)',
  low: 'rgba(34, 211, 238, 0.28)',
}
const BASE = 'rgba(148, 197, 218, 0.05)'
const OUTLINE = 'rgba(148, 197, 218, 0.4)'
const HIGHLIGHT = '#ff9d5c'

export const ORGAN_LABELS = {
  brain: 'Brain', heart: 'Heart', lungs: 'Lungs', liver: 'Liver', stomach: 'Stomach',
  intestines: 'Intestines', kidneys: 'Kidneys', pancreas: 'Pancreas',
  blood_vessels: 'Blood vessels', muscle: 'Muscle', skin: 'Skin', fat: 'Fat',
  thyroid: 'Thyroid', spleen: 'Spleen', bladder: 'Bladder',
}

function fillFor(entry, hatchPrefix) {
  if (!entry || !LEVEL_COLORS[entry.level]) return 'none'
  return entry.basis === 'rna' ? `url(#${hatchPrefix}-${entry.level})` : LEVEL_COLORS[entry.level]
}

export default function BodyMap({ bodyMap = {}, selected, highlight, onSelect }) {
  const uid = useId()
  const hatchPrefix = `hatch${uid}`
  const glowId = `glow${uid}`

  const organProps = (key) => {
    const entry = bodyMap[key]
    const isHighlight = highlight === key
    return {
      id: key,
      className: ['organ', selected === key && 'selected', isHighlight && 'highlight']
        .filter(Boolean).join(' '),
      fill: isHighlight ? HIGHLIGHT : fillFor(entry, hatchPrefix),
      stroke: isHighlight ? HIGHLIGHT : OUTLINE,
      strokeWidth: isHighlight ? 2.5 : 1.5,
      filter: isHighlight || entry ? `url(#${glowId})` : undefined,
      onClick: onSelect ? () => onSelect(key) : undefined,
      'aria-label': ORGAN_LABELS[key],
      role: onSelect ? 'button' : undefined,
    }
  }
  const skin = bodyMap.skin

  return (
    <svg viewBox="0 0 200 420" className="body-map" role="img" aria-label="Body map">
      <defs>
        <filter id={glowId} x="-75%" y="-75%" width="250%" height="250%">
          <feGaussianBlur stdDeviation="3.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        {Object.entries(LEVEL_COLORS).map(([level, color]) => (
          <pattern key={level} id={`${hatchPrefix}-${level}`} width="6" height="6"
                   patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="6" height="6" fill="transparent" />
            <rect width="3" height="6" fill={color} />
          </pattern>
        ))}
      </defs>

      <g {...organProps('skin')} fill={skin ? fillFor(skin, hatchPrefix) : BASE}>
        <circle cx="100" cy="40" r="32" />
        <rect x="88" y="68" width="24" height="22" />
        <rect x="58" y="86" width="84" height="210" rx="34" />
        <rect x="30" y="96" width="24" height="150" rx="12" />
        <rect x="146" y="96" width="24" height="150" rx="12" />
        <rect x="64" y="270" width="32" height="140" rx="14" />
        <rect x="104" y="270" width="32" height="140" rx="14" />
      </g>

      <g {...organProps('fat')}>
        <ellipse cx="70" cy="252" rx="8" ry="16" />
        <ellipse cx="130" cy="252" rx="8" ry="16" />
      </g>
      <g {...organProps('muscle')}>
        <ellipse cx="80" cy="335" rx="11" ry="34" />
        <ellipse cx="120" cy="335" rx="11" ry="34" />
        <ellipse cx="42" cy="140" rx="8" ry="26" />
        <ellipse cx="158" cy="140" rx="8" ry="26" />
      </g>
      <path {...organProps('blood_vessels')} fill="none"
            stroke={highlight === 'blood_vessels' ? HIGHLIGHT : bodyMap.blood_vessels ? LEVEL_COLORS[bodyMap.blood_vessels.level] : OUTLINE}
            strokeWidth={highlight === 'blood_vessels' ? 4 : 2.5} strokeLinecap="round"
            strokeDasharray={bodyMap.blood_vessels?.basis === 'rna' ? '6 4' : undefined}
            d="M100 150 V255 M100 255 L82 300 V395 M100 255 L118 300 V395 M100 108 L48 120 V230 M100 108 L152 120 V230" />
      <ellipse {...organProps('brain')} cx="100" cy="36" rx="22" ry="18" />
      <ellipse {...organProps('thyroid')} cx="100" cy="84" rx="10" ry="5" />
      <g {...organProps('lungs')}>
        <ellipse cx="80" cy="135" rx="16" ry="28" />
        <ellipse cx="120" cy="135" rx="16" ry="28" />
      </g>
      <path {...organProps('heart')}
            d="M106 160 C92 150 92 136 100 134 C104 133 106 136 106 138 C106 136 108 133 112 134 C120 136 120 150 106 160 Z" />
      <ellipse {...organProps('liver')} cx="82" cy="180" rx="24" ry="13" />
      <ellipse {...organProps('stomach')} cx="118" cy="184" rx="14" ry="12" />
      <ellipse {...organProps('spleen')} cx="138" cy="176" rx="6" ry="10" />
      <ellipse {...organProps('pancreas')} cx="104" cy="202" rx="18" ry="5" />
      <g {...organProps('kidneys')}>
        <ellipse cx="80" cy="214" rx="7" ry="11" />
        <ellipse cx="120" cy="214" rx="7" ry="11" />
      </g>
      <rect {...organProps('intestines')} x="78" y="226" width="44" height="40" rx="14" />
      <ellipse {...organProps('bladder')} cx="100" cy="280" rx="11" ry="8" />
    </svg>
  )
}

export function BodyLegend() {
  return (
    <div className="legend">
      {Object.entries(LEVEL_COLORS).map(([level, color]) => (
        <span key={level}><i style={{ background: color }} />{level}</span>
      ))}
      <span><i className="hatched" />based on RNA (no protein data)</span>
    </div>
  )
}
