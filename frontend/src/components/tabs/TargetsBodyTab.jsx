import { useState } from 'react'
import Body3D, { BodyLegend } from '../Body3D.jsx'
import BodySexToggle from '../BodySexToggle.jsx'
import { useBodySex } from '../../lib/bodySex.js'
import TargetsTab from './TargetsTab.jsx'
import { ORGAN_LABELS } from '../../lib/organs.js'

// Body map and target list side by side: picking an organ highlights the targets found there.
export default function TargetsBodyTab({ drug }) {
  const [selected, setSelected] = useState(null)
  const [sex] = useBodySex()
  const entry = selected && drug.body_map[selected]

  if (!drug.targets.length) return <p>No known protein targets recorded.</p>

  return (
    <div className="tab-grid body-tab">
      <div className="card center body-sticky">
        <BodySexToggle />
        <Body3D bodyMap={drug.body_map} selected={selected} onSelect={setSelected} fit={1.08} sex={sex} />
        <BodyLegend />
      </div>
      <div className="stack">
        <div className="card">
          <h3>Where the targets are found</h3>
          {!selected && <p className="muted">Click an organ to see which targets shade it.</p>}
          {selected && !entry && <p>{ORGAN_LABELS[selected]}: no targets detected here.</p>}
          {entry && (
            <p>
              <strong>{ORGAN_LABELS[selected]}</strong>: {entry.level} level
              {entry.basis === 'rna' && ' (estimated from RNA)'}. Matching targets are highlighted below.
            </p>
          )}
        </div>
        <TargetsTab drug={drug} activeGenes={entry ? entry.targets : null} />
      </div>
    </div>
  )
}
