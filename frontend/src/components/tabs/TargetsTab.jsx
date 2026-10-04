export default function TargetsTab({ drug }) {
  if (!drug.targets.length) return <p>No known protein targets recorded.</p>
  return (
    <div className="stack">
      {drug.targets.map((target) => (
        <div key={target.gene} className="card target">
          <div>
            <h3>{target.name} <span className="pill">{target.gene}</span></h3>
            <p>{target.plain_description}</p>
          </div>
          <span className="pill action">{target.action}</span>
        </div>
      ))}
      <p className="muted">A 3D view of the drug inside its target (Mol*) goes here when a structure exists.</p>
    </div>
  )
}
