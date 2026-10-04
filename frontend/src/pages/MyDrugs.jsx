import { Link } from 'react-router-dom'
import { DEMO_EFFECT_RULES, displayName, findDemoDrug } from '../demo/demoData.js'
import { checkInteractions } from '../lib/interactions.js'
import { MAX_DRUGS, useMyDrugs } from '../lib/myDrugs.js'

export default function MyDrugs() {
  const myDrugs = useMyDrugs()
  const drugs = myDrugs.list.map(findDemoDrug).filter(Boolean)
  const result = drugs.length >= 2 ? checkInteractions(drugs, DEMO_EFFECT_RULES) : null
  const nameOf = (rxcui) => findDemoDrug(rxcui)?.brands[0] ?? rxcui

  return (
    <section>
      <h1>My Drugs</h1>
      {!myDrugs.persistent && (
        <p className="note">Your browser isn't saving data, so this list lasts for this visit only.</p>
      )}
      {!drugs.length && (
        <p className="muted">No drugs saved yet. Open a drug from <Link to="/">Home</Link> and add it (up to {MAX_DRUGS}).</p>
      )}
      <div className="stack">
        {drugs.map((d) => (
          <div key={d.rxcui} className="card row">
            <Link to={`/drug/${d.rxcui}`}><strong>{displayName(d)}</strong></Link>
            <button className="ghost" onClick={() => myDrugs.remove(d.rxcui)}>Remove</button>
          </div>
        ))}
      </div>

      {drugs.length === 1 && <p className="muted">Add another drug to check for interactions.</p>}
      {result && (
        <>
          <h2>Interaction check</h2>
          {!result.findings.length && <p>No interactions found between these drugs in our data.</p>}
          <div className="stack">
            {result.findings.map((f, i) => (
              <div key={i} className={`card finding ${f.severity}`}>
                <div className="row">
                  <strong>{f.drugs.map(nameOf).join(' + ')}</strong>
                  <span className={`pill severity ${f.severity}`}>{f.severity}</span>
                </div>
                <p>{f.plain_message}</p>
                <p className="muted small">Why: {f.mechanism} ({f.type})</p>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  )
}
