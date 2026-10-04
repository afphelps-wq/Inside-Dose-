import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { DEMO_DRUGS, displayName } from '../demo/demoData.js'

export default function Home() {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()
  const q = query.trim().toLowerCase()
  const matches = q
    ? DEMO_DRUGS.filter((d) => [d.generic, ...d.brands].some((name) => name.toLowerCase().includes(q))).slice(0, 10)
    : []

  return (
    <section>
      <div className="hero">
        <h1>See how a drug works inside your body</h1>
        <p className="muted">Search a medicine to explore its molecule, the proteins it acts on, and its journey through you.</p>
        <div className="search">
          <input
            type="search" placeholder="Search by brand or generic name (try “sam”)"
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
      <div className="gallery">
        {DEMO_DRUGS.map((d) => (
          <Link key={d.rxcui} to={`/drug/${d.rxcui}`} className="card drug-card">
            <span className="pill">{d.common_use}</span>
            <h3>{d.brands[0]}</h3>
            <p className="muted">{d.generic}</p>
          </Link>
        ))}
      </div>
    </section>
  )
}
