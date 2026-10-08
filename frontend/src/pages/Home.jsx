import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getCuratedDrugs, searchDrugs } from '../api/client.js'
import HeroArt from '../components/home/HeroArt.jsx'
import '../home.css'

function displayName(drug) {
  const brand = drug.brand || drug.brands?.[0]
  return brand ? `${brand} (${drug.generic})` : drug.generic
}

const SEARCH_DEBOUNCE_MS = 250

const scrollToId = (id) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })

function Arrow() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" className="h-icon">
      <path d="M3 8 H13 M9 4 L13 8 L9 12" />
    </svg>
  )
}

export default function Home() {
  const [drugs, setDrugs] = useState(null)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState('')
  const [matches, setMatches] = useState([])
  const [searching, setSearching] = useState(false)
  const navigate = useNavigate()
  const searchRef = useRef(null)

  useEffect(() => {
    const controller = new AbortController()
    getCuratedDrugs({ signal: controller.signal })
      .then(setDrugs)
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message) })
    return () => controller.abort()
  }, [])

  const q = query.trim()
  useEffect(() => {
    if (!q) {
      setMatches([])
      setSearching(false)
      return
    }
    setSearching(true)
    const controller = new AbortController()
    const timer = setTimeout(() => {
      searchDrugs(q, { signal: controller.signal })
        .then((results) => { setMatches(results); setSearching(false) })
        .catch((err) => { if (err.name !== 'AbortError') setSearching(false) })
    }, SEARCH_DEBOUNCE_MS)
    return () => { clearTimeout(timer); controller.abort() }
  }, [q])

  return (
    <div className="home">
      <div className="h-page">
        <section className="h-hero" aria-label="Introduction">
          <div className="h-glow" aria-hidden="true" />
          <div className="h-art" aria-hidden="true"><HeroArt /></div>

          <h1 className="h-title">
            <span className="h-title-1">Inside<span aria-hidden="true" className="h-pillbar" /></span>
            <span className="h-title-2">Dose <span className="h-outline">Rx.</span></span>
          </h1>

          <div className="h-left">
            <div className="h-tagline">
              <span>How medicine moves<br />through your body</span>
              <span aria-hidden="true" className="h-rule" />
              <span className="h-year">2026</span>
            </div>
            <div className="h-browse">
              <button type="button" className="h-circle" aria-label="Browse curated drugs" onClick={() => scrollToId('gallery')}>
                <svg width="18" height="18" viewBox="0 0 16 16" aria-hidden="true" className="h-icon"><path d="M3 8 H13 M9 4 L13 8 L9 12" /></svg>
              </button>
              <span>Browse {drugs ? drugs.length : 20}<br />curated drugs</span>
            </div>
            <p className="h-blurb">See the molecule, the proteins it targets, where it goes in your body, and how it leaves.</p>
          </div>

          <div className="h-right">
            <div className="h-prompt">
              Type any <span className="h-hl">drug</span>,<br />brand or generic,<br />and follow it inside.
            </div>
            <div className="h-searchbox">
              <label htmlFor="hq" className="h-sr">Search a drug by brand or generic name</label>
              <svg width="20" height="20" viewBox="0 0 16 16" aria-hidden="true" className="h-searchicon"><circle cx="7" cy="7" r="5" /><path d="M11 11 L15 15" /></svg>
              <input
                id="hq" ref={searchRef} className="h-search" type="search" autoComplete="off"
                placeholder="e.g. Lipitor or ibuprofen"
                value={query} onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && matches[0]) navigate(`/drug/${matches[0].rxcui}`) }}
              />
              {q && (
                <div className="h-results" role="listbox" aria-label="Matching drugs">
                  {searching && <div className="h-result-note">Searching…</div>}
                  {!searching && !matches.length && <div className="h-result-note">We couldn't find that drug.</div>}
                  {!searching && matches.map((d) => (
                    <Link key={d.rxcui} to={`/drug/${d.rxcui}`} className="h-result" role="option">
                      <span>{displayName(d)}</span>
                      <span className={d.curated ? 'h-badge ok' : 'h-badge'}>{d.curated ? 'Curated' : 'Basic info only'}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
            <div className="h-hint">Any drug: molecule, targets and body map.<br />Curated drugs add the full journey.</div>
          </div>

          <div className="h-actions">
            <span className="h-privacy">
              <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" className="h-lock"><rect x="3" y="7" width="10" height="7" rx="2" /><path d="M5.5 7 V5 a2.5 2.5 0 0 1 5 0 V7" /></svg>
              Nothing you save leaves your browser
            </span>
            <div className="h-btns">
              <button type="button" className="h-cta" onClick={() => searchRef.current?.focus()}>Get started <Arrow /></button>
            </div>
          </div>
        </section>

        <section id="gallery" className="h-gallery" aria-labelledby="galleryTitle">
          <div className="h-gallery-head">
            <div>
              <div className="h-lbl">Curated · full journey</div>
              <h2 id="galleryTitle">The most-prescribed drugs</h2>
            </div>
            <p>Hand-checked against FDA labels. Each one includes the blood-level curve, the journey through the body, and interaction checks.</p>
          </div>
          {error && <p className="h-error">Couldn't load the drug list: {error}</p>}
          {!error && !drugs && <p className="h-loading">Loading curated drugs…</p>}
          {drugs && (
            <div className="h-grid">
              {drugs.map((d) => (
                <Link key={d.rxcui} to={`/drug/${d.rxcui}`} className="h-card">
                  <span className="h-dot">{d.generic.charAt(0).toUpperCase()}</span>
                  <span className="h-card-generic">{d.generic}</span>
                  <span className="h-card-brand">{d.brands[0] || d.generic}</span>
                  <span className="h-card-use">{d.common_use}</span>
                </Link>
              ))}
            </div>
          )}
        </section>

        <footer className="h-footer">
          <span className="h-disclaimer">Educational, not medical advice. Values are population averages from FDA labels.</span>
          <span>Data: DailyMed · RxNorm · PubChem · ChEMBL · RCSB PDB · Human Protein Atlas (CC BY-SA)</span>
        </footer>
      </div>
    </div>
  )
}
