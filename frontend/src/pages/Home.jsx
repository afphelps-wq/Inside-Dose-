import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getCuratedDrugs } from '../api/client.js'

function displayName(drug) {
  return drug.brands?.length ? `${drug.brands[0]} (${drug.generic})` : drug.generic
}

export default function Home() {
  const [drugs, setDrugs] = useState(null)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const controller = new AbortController()
    getCuratedDrugs({ signal: controller.signal })
      .then(setDrugs)
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message) })
    return () => controller.abort()
  }, [])

  const q = query.trim().toLowerCase()
  const matches = q && drugs
    ? drugs.filter((d) => [d.generic, ...d.brands].some((name) => name.toLowerCase().includes(q))).slice(0, 10)
    : []

  return (
    <section>
      <div className="hero">
        <h1>See how a drug works inside your body</h1>
        <p className="muted">Search a medicine to explore its molecule, the proteins it acts on, and its journey through you.</p>
        <div className="search">
          <input
            type="search" placeholder="Search by brand or generic name"
            value={query} onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && matches[0]) navigate(`/drug/${matches[0].rxcui}`) }}
            aria-label="Search drugs"
          />
          {q && (
            <ul className="suggestions">
              {matches.length
                ? matches.map((d) => <li key={d.rxcui}><Link to={`/drug/${d.rxcui}`}>{displayName(d)}</Link></li>)
                : <li className="muted">We couldn't find that drug.</li>}
            </ul>
          )}
        </div>
      </div>

      <h2>Explore curated drugs</h2>
      {error && <p className="error-banner">Couldn't load the drug list: {error}</p>}
      {!error && !drugs && <p className="loading-state">Loading curated drugs…</p>}
      {drugs && (
        <div className="gallery">
          {drugs.map((d) => (
            <Link key={d.rxcui} to={`/drug/${d.rxcui}`} className="card drug-card">
              <span className="pill">{d.common_use}</span>
              <h3>{d.brands[0] || d.generic}</h3>
              <p className="muted">{d.generic}</p>
            </Link>
          ))}
        </div>
      )}
    </section>
  )
}
