import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import JourneyTab from '../components/tabs/JourneyTab.jsx'
import MoleculeTab from '../components/tabs/MoleculeTab.jsx'
import TargetsBodyTab from '../components/tabs/TargetsBodyTab.jsx'
import { getDrug } from '../api/client.js'
import { MAX_DRUGS, useMyDrugs } from '../lib/myDrugs.js'

const TABS = [
  { key: 'molecule', label: 'Molecule' },
  { key: 'targets', label: 'Targets & Body' },
  { key: 'journey', label: 'Journey', curatedOnly: true },
]

export default function Drug() {
  const { rxcui } = useParams()
  const [bundle, setBundle] = useState(null)
  const [error, setError] = useState(null)
  const [tab, setTab] = useState('molecule')
  const myDrugs = useMyDrugs()

  useEffect(() => {
    setBundle(null)
    setError(null)
    setTab('molecule')
    const controller = new AbortController()
    getDrug(rxcui, { signal: controller.signal })
      .then(setBundle)
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message) })
    return () => controller.abort()
  }, [rxcui])

  if (error) {
    return (
      <section>
        <h1>We couldn't find that drug.</h1>
        <p className="muted">{error}</p>
        <Link to="/">Back to search</Link>
      </section>
    )
  }

  if (!bundle) {
    return <p className="loading-state">Loading drug…</p>
  }

  const tabs = TABS.filter((t) => !t.curatedOnly || bundle.curated)
  const activeTab = tabs.find((t) => t.key === tab) || tabs[0]
  const saved = myDrugs.has(bundle.rxcui)
  const full = myDrugs.list.length >= MAX_DRUGS

  return (
    <section>
      <div className="drug-header">
        <div>
          <h1>{bundle.brands[0] || bundle.generic} <span className="muted">({bundle.generic})</span></h1>
          {bundle.curated && <span className="pill">{bundle.curated.common_use}</span>}
          {!bundle.curated && <span className="pill">Basic info only</span>}
        </div>
        <button onClick={() => (saved ? myDrugs.remove(bundle.rxcui) : myDrugs.add(bundle.rxcui))}
                disabled={!saved && full}>
          {saved ? '✓ In My Drugs' : full ? 'My Drugs is full (5)' : '+ Add to My Drugs'}
        </button>
      </div>
      {bundle.stale && <p className="note">Data may be out of date -- couldn't reach the live source just now.</p>}
      <div className="tabs" role="tablist">
        {tabs.map((t) => (
          <button key={t.key} role="tab" aria-selected={t.key === tab}
                  className={t.key === tab ? 'tab active' : 'tab'} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>
      {activeTab.key === 'molecule' && <MoleculeTab rxcui={bundle.rxcui} molecule={bundle.molecule} />}
      {activeTab.key === 'targets' && <TargetsBodyTab drug={bundle} />}
      {activeTab.key === 'journey' && bundle.curated && <JourneyTab curated={bundle.curated} />}
      {bundle.sources.length > 0 && (
        <p className="sources muted small">
          Data from: {bundle.sources.map((s, i) => (
            <span key={s.name}>
              {i > 0 && ', '}
              <a href={s.url} target="_blank" rel="noreferrer">{s.name}</a>
            </span>
          ))}
        </p>
      )}
    </section>
  )
}
