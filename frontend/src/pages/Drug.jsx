import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import BodyTab from '../components/tabs/BodyTab.jsx'
import JourneyTab from '../components/tabs/JourneyTab.jsx'
import MoleculeTab from '../components/tabs/MoleculeTab.jsx'
import TargetsTab from '../components/tabs/TargetsTab.jsx'
import { findDemoDrug } from '../demo/demoData.js'
import { MAX_DRUGS, useMyDrugs } from '../lib/myDrugs.js'

const TABS = [
  { key: 'molecule', label: 'Molecule', Component: MoleculeTab },
  { key: 'targets', label: 'Targets', Component: TargetsTab },
  { key: 'body', label: 'Body', Component: BodyTab },
  { key: 'journey', label: 'Journey', Component: JourneyTab, curatedOnly: true },
]

export default function Drug() {
  const { rxcui } = useParams()
  const drug = findDemoDrug(rxcui)
  const [tab, setTab] = useState('molecule')
  const myDrugs = useMyDrugs()

  if (!drug) {
    return (
      <section>
        <h1>We couldn't find that drug.</h1>
        <Link to="/">Back to search</Link>
      </section>
    )
  }

  const tabs = TABS.filter((t) => !t.curatedOnly || drug.curated)
  const { Component } = tabs.find((t) => t.key === tab) || tabs[0]
  const saved = myDrugs.has(drug.rxcui)
  const full = myDrugs.list.length >= MAX_DRUGS

  return (
    <section>
      <div className="drug-header">
        <div>
          <h1>{drug.brands[0]} <span className="muted">({drug.generic})</span></h1>
          <span className="pill">{drug.common_use}</span>
          {!drug.curated && <span className="pill">Basic info only</span>}
        </div>
        <button onClick={() => (saved ? myDrugs.remove(drug.rxcui) : myDrugs.add(drug.rxcui))}
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
      <Component key={drug.rxcui} drug={drug} />
    </section>
  )
}
