import { useState } from 'react'
import BodyMap, { BodyLegend, ORGAN_LABELS } from '../BodyMap.jsx'

export default function BodyTab({ drug }) {
  const [selected, setSelected] = useState(null)
  const entry = selected && drug.body_map[selected]
  const targets = entry ? drug.targets.filter((t) => entry.targets.includes(t.gene)) : []

  return (
    <div className="tab-grid">
      <div className="card center">
        <BodyMap bodyMap={drug.body_map} selected={selected} onSelect={setSelected} />
        <BodyLegend />
      </div>
      <div className="card">
        <h3>Where the targets are found</h3>
        {!selected && <p className="muted">Click an organ to see which targets shade it.</p>}
        {selected && !entry && <p>{ORGAN_LABELS[selected]}: no targets detected here.</p>}
        {entry && (
          <>
            <p>
              <strong>{ORGAN_LABELS[selected]}</strong>: {entry.level} level
              {entry.basis === 'rna' && ' (estimated from RNA)'}
            </p>
            <ul>
              {targets.map((t) => <li key={t.gene}><strong>{t.gene}</strong>: {t.plain_description}</li>)}
            </ul>
          </>
        )}
      </div>
    </div>
  )
}
