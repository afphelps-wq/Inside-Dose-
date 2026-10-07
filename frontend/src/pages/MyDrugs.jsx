import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDrug, postInteractions } from '../api/client.js'
import { MAX_DRUGS, useMyDrugs } from '../lib/myDrugs.js'

function displayName(bundle) {
  return bundle.brands?.length ? `${bundle.brands[0]} (${bundle.generic})` : bundle.generic
}

export default function MyDrugs() {
  const myDrugs = useMyDrugs()
  const [bundles, setBundles] = useState({})
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const controller = new AbortController()
    Promise.all(myDrugs.list.map((rxcui) => getDrug(rxcui, { signal: controller.signal })))
      .then((loaded) => setBundles(Object.fromEntries(loaded.map((b) => [b.rxcui, b]))))
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message) })
    return () => controller.abort()
  }, [myDrugs.list])

  useEffect(() => {
    setResult(null)
    if (myDrugs.list.length < 2) return
    const controller = new AbortController()
    postInteractions(myDrugs.list, { signal: controller.signal })
      .then(setResult)
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message) })
    return () => controller.abort()
  }, [myDrugs.list])

  const nameOf = (rxcui) => (bundles[rxcui] ? displayName(bundles[rxcui]) : rxcui)

  return (
    <section>
      <h1>My Drugs</h1>
      {!myDrugs.persistent && (
        <p className="note">Your browser isn't saving data, so this list lasts for this visit only.</p>
      )}
      {error && <p className="error-banner">{error}</p>}
      {!myDrugs.list.length && (
        <p className="muted">No drugs saved yet. Open a drug from <Link to="/">Home</Link> and add it (up to {MAX_DRUGS}).</p>
      )}
      <div className="stack">
        {myDrugs.list.map((rxcui) => (
          <div key={rxcui} className="card row">
            <Link to={`/drug/${rxcui}`}><strong>{nameOf(rxcui)}</strong></Link>
            <button className="ghost" onClick={() => myDrugs.remove(rxcui)}>Remove</button>
          </div>
        ))}
      </div>

      {myDrugs.list.length === 1 && <p className="muted">Add another drug to check for interactions.</p>}
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
          {result.unchecked.length > 0 && (
            <p className="muted small">No data — not checked: {result.unchecked.map(nameOf).join(', ')}</p>
          )}
        </>
      )}
    </section>
  )
}
