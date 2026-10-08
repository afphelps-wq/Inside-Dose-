import StructureViewer from '../StructureViewer.jsx'

export default function TargetsTab({ drug, activeGenes = null }) {
  if (!drug.targets.length) return <p>No known protein targets recorded.</p>
  return (
    <div className="stack">
      {drug.targets.map((target) => (
        <div key={target.gene} className={`card${activeGenes?.includes(target.gene) ? ' target-active' : ''}${activeGenes && !activeGenes.includes(target.gene) ? ' target-dim' : ''}`}>
          <div className="target">
            <div>
              <h3>{target.name} <span className="pill">{target.gene}</span></h3>
              <p>{target.plain_description}</p>
            </div>
            <span className="pill action">{target.action}</span>
          </div>
          {target.uniprot && <StructureViewer uniprot={target.uniprot} rxcui={drug.rxcui} />}
        </div>
      ))}
    </div>
  )
}
