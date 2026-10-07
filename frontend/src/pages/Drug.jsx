import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import BodyTab from '../components/tabs/BodyTab.jsx'
import MoleculeTab from '../components/tabs/MoleculeTab.jsx'
import TargetsTab from '../components/tabs/TargetsTab.jsx'
import { ORGAN_LABELS } from '../components/BodyMap.jsx'
import { getDrug } from '../api/client.js'
import { MAX_DRUGS, useMyDrugs } from '../lib/myDrugs.js'

// Static read of the curated journey steps. The interactive version (dosing
// sliders, animation, concentration curve) is M4 -- this just surfaces the
// real curated text, which is already there, without pretending to be M4.
function JourneyPreview({ curated }) {
  return (
    <div className="card">
      <h3>The drug's journey</h3>
      <ol className="journey">
        {curated.journey.map((step, i) => (
          <li key={i}>
            <span className="step-name">{step.step}</span>
            <span className="muted"> · {ORGAN_LABELS[step.organ]}</span>
            <p>{step.text}</p>
          </li>
        ))}
      </ol>
      <p className="muted small">Dosing sliders and the concentration-over-time curve are coming next.</p>
    </div>
  )
}

const TABS = [
  { key: 'molecule', label: 'Molecule' },
  { key: 'targets', label: 'Targets' },
  { key: 'body', label: 'Body' },
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
      <div className="tabs" role="tablist">
        {tabs.map((t) => (
          <button key={t.key} role="tab" aria-selected={t.key === tab}
                  className={t.key === tab ? 'tab active' : 'tab'} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>
      {activeTab.key === 'molecule' && <MoleculeTab rxcui={bundle.rxcui} molecule={bundle.molecule} />}
      {activeTab.key === 'targets' && <TargetsTab drug={bundle} />}
      {activeTab.key === 'body' && <BodyTab drug={bundle} />}
      {activeTab.key === 'journey' && bundle.curated && <JourneyPreview curated={bundle.curated} />}
    </section>
  )
}
