export default function MoleculeTab({ drug }) {
  return (
    <div className="tab-grid">
      <div className="card molecule-placeholder">
        <svg viewBox="0 0 200 140" aria-hidden="true">
          <g className="bonds">
            <line x1="60" y1="70" x2="100" y2="45" /><line x1="100" y1="45" x2="140" y2="70" />
            <line x1="140" y1="70" x2="140" y2="110" /><line x1="60" y1="70" x2="60" y2="110" />
            <line x1="100" y1="45" x2="100" y2="12" /><line x1="140" y1="70" x2="175" y2="52" />
          </g>
          <circle cx="60" cy="70" r="12" className="atom c" /><circle cx="100" cy="45" r="12" className="atom c" />
          <circle cx="140" cy="70" r="12" className="atom n" /><circle cx="140" cy="110" r="10" className="atom c" />
          <circle cx="60" cy="110" r="10" className="atom o" /><circle cx="100" cy="12" r="8" className="atom h" />
          <circle cx="175" cy="52" r="10" className="atom o" />
        </svg>
        <p className="muted">The rotatable 3D structure (3Dmol.js) goes here.</p>
      </div>
      <div className="card">
        <h3>Key properties</h3>
        <dl className="props">
          <dt>Formula</dt><dd>{drug.molecule.formula}</dd>
          <dt>Molecular weight</dt><dd>{drug.molecule.weight} g/mol</dd>
        </dl>
      </div>
    </div>
  )
}
