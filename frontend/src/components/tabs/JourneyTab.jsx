import { useEffect, useMemo, useState } from 'react'
import { concentrationCurve } from '../../lib/pk.js'
import { ORGAN_LABELS } from '../../lib/organs.js'
import Body3D from '../Body3D.jsx'
import BodySexToggle from '../BodySexToggle.jsx'
import { useBodySex } from '../../lib/bodySex.js'
import '../../journey.css'

const pretty = (s) => String(s).replace(/_/g, ' ')
const fmt = (v) => (v >= 100 ? v.toFixed(0) : v >= 10 ? v.toFixed(1) : v >= 1 ? v.toFixed(2) : Number(v.toPrecision(2)).toString())

function niceTicks(max, count) {
  const raw = max / count
  const mag = 10 ** Math.floor(Math.log10(raw))
  const step = [1, 2, 5, 10].map((m) => m * mag).find((s) => s >= raw)
  const out = []
  for (let v = 0; v <= max + 1e-9; v += step) out.push(Number(v.toFixed(10)))
  return out
}

function pkTiles(pk) {
  const range = (m) => (m.range[0] === m.range[1] ? `${m.range[0]}` : `${m.range[0]}–${m.range[1]}`)
  return [
    { label: 'Bioavailability', value: Math.round(pk.bioavailability.model * 100), unit: '%', range: `${Math.round(pk.bioavailability.range[0] * 100)}–${Math.round(pk.bioavailability.range[1] * 100)}%` },
    { label: 'Half-life', value: pk.half_life.model, unit: 'h', range: `${range(pk.half_life)} h` },
    { label: 'Volume of dist.', value: pk.vd.model, unit: pk.vd.unit, range: `${range(pk.vd)} ${pk.vd.unit}` },
    { label: 'Time to peak', value: pk.tmax.model, unit: 'h', range: `${range(pk.tmax)} h` },
  ]
}

function BloodLevel({ curve, intervalH, scrub, setScrub }) {
  const { points, windowH } = curve
  const maxC = Math.max(...points.map((p) => p.c)) * 1.1 || 1
  const firstDose = points.filter((p) => p.t <= intervalH)
  const peak = firstDose.reduce((a, p) => (p.c > a.c ? p : a), firstDose[0])
  const yTicks = niceTicks(maxC, 4)
  const xTicks = niceTicks(windowH, 5)
  const sx = (t) => (t / windowH) * 1000
  const sy = (c) => 240 - (c / maxC) * 240
  const line = points.map((p, i) => `${i ? 'L' : 'M'}${sx(p.t).toFixed(1)},${sy(p.c).toFixed(1)}`).join('')
  const area = `${line}L1000,240L0,240Z`

  const idx = Math.round((scrub / 1000) * (points.length - 1))
  const at = points[idx]

  return (
    <div className="jt-chart-col">
      <div className="jt-readout">
        <div className="lbl">Estimated blood level (population average) · mg/L</div>
        <div className="jt-readout-vals">
          <span><span className="mono">{at.t.toFixed(1)}</span><small>h</small></span>
          <span><span className="mono acc">{fmt(at.c)}</span><small>mg/L</small></span>
        </div>
      </div>
      <div className="jt-plot">
        <div className="jt-yaxis">
          {yTicks.map((c) => <span key={c} style={{ bottom: `${(c / maxC) * 100}%` }}>{c}</span>)}
        </div>
        <div className="jt-canvas">
          {yTicks.map((c) => <div key={c} className="jt-gridline" style={{ bottom: `${(c / maxC) * 100}%` }} />)}
          <svg viewBox="0 0 1000 240" preserveAspectRatio="none" role="img" aria-label="Estimated blood level over time">
            <path className="jt-area" d={area} />
            <path className="jt-curve" d={line} />
          </svg>
          <div className="jt-cursor" style={{ left: `${(at.t / windowH) * 100}%` }} />
          <div className="jt-dot" style={{ left: `${(at.t / windowH) * 100}%`, bottom: `${(at.c / maxC) * 100}%` }} />
        </div>
        <div />
        <div className="jt-xaxis">
          {xTicks.map((t) => <span key={t} style={{ left: `${(t / windowH) * 100}%` }}>{t}</span>)}
        </div>
      </div>
      <div className="jt-scrub">
        <label htmlFor="jt-scrub" className="lbl">Time</label>
        <input id="jt-scrub" className="jt-range" type="range" min="0" max="1000" step="1"
               value={scrub} onChange={(e) => setScrub(Number(e.target.value))} />
      </div>
      <div className="jt-foot mono">
        First-dose peak ≈ {fmt(peak.c)} mg/L at {peak.t.toFixed(1)} h · window {windowH} h · one-compartment oral model
      </div>
    </div>
  )
}

export default function JourneyTab({ curated }) {
  const { journey } = curated
  const formulation = curated.formulations[0]
  const dose = formulation.dose_mg
  const pk = formulation.pk
  const perKg = pk.vd.unit === 'L/kg'

  const [doseMg, setDoseMg] = useState(dose.typical)
  const [intervalH, setIntervalH] = useState(dose.intervals_h[0])
  const [weightKg, setWeightKg] = useState(70)
  const [step, setStep] = useState(0)
  const [playing, setPlaying] = useState(true)
  const [scrub, setScrub] = useState(null)
  const [sex] = useBodySex()

  useEffect(() => {
    if (!playing) return
    const timer = setInterval(() => setStep((s) => (s + 1) % journey.length), 1800)
    return () => clearInterval(timer)
  }, [playing, journey.length])

  const curve = useMemo(
    () => concentrationCurve({
      doseMg,
      intervalH,
      weightKg: perKg ? weightKg : 70,
      pk: {
        bioavailability: pk.bioavailability.model,
        half_life: pk.half_life.model,
        vd: pk.vd.model,
        vd_unit: pk.vd.unit,
        tmax: pk.tmax.model,
      },
    }),
    [doseMg, intervalH, weightKg, perKg, pk],
  )

  // Until the user scrubs, park the cursor on the first-dose peak.
  const peakScrub = useMemo(() => {
    const { points } = curve
    const i = points.reduce((best, p, k) => (p.t <= intervalH && p.c > points[best].c ? k : best), 0)
    return Math.round((i / (points.length - 1)) * 1000)
  }, [curve, intervalH])

  const active = journey[step]
  const pick = (i) => { setStep(i); setPlaying(false) }
  const enzymes = [...(curated.enzymes || []), ...(curated.transporters || [])]
  const routes = curated.elimination?.routes || []
  const effects = curated.effects || []

  return (
    <div className="jt">
      <div className="jt-main">
        <section className="jt-col" aria-label="Pharmacokinetics">
          <div className="panel jt-tiles">
            {pkTiles(pk).map((t) => (
              <div key={t.label}>
                <div className="lbl">{t.label}</div>
                <div className="jt-tile-val"><span className="mono">{t.value}</span><span>{t.unit}</span></div>
                <div className="jt-tile-range mono">label {t.range}</div>
              </div>
            ))}
          </div>
          <div className="panel jt-facts">
            <div className="lbl">Enzymes &amp; transporters</div>
            {enzymes.length === 0 && <div className="jt-row"><span>None significant on label</span></div>}
            {enzymes.map((e) => (
              <div className="jt-row" key={e.name}>
                <b className="mono">{e.name}</b>
                <span>{e.role} · {e.importance || e.strength || '—'}</span>
              </div>
            ))}
            <div className="jt-sep" />
            <div className="lbl">Elimination</div>
            {routes.map((r) => (
              <div className="jt-row" key={r.route}>
                <b>{pretty(r.route)}</b>
                <span className="mono">{r.fraction != null ? `${Math.round(r.fraction * 100)}%` : 'primary'}</span>
              </div>
            ))}
            {effects.length > 0 && (
              <>
                <div className="jt-sep" />
                <div className="lbl">Effect categories</div>
                <div className="jt-badges">
                  {effects.map((e) => <span className="jt-badge" key={e.category}>{pretty(e.category)}</span>)}
                </div>
              </>
            )}
          </div>
          <div className="panel">
            <BloodLevel curve={curve} intervalH={intervalH} scrub={scrub ?? peakScrub} setScrub={setScrub} />
          </div>
          <p className="jt-note mono">Source: FDA label via DailyMed · §2, §12.3</p>
        </section>

        <section className="panel jt-body" aria-label="Body model">
          <div className="jt-body-head lbl">
            <span>Journey · population average</span>
            <span>Step <em>{step + 1}/{journey.length}</em></span>
          </div>
          <BodySexToggle />
          <div className="jt-stage"><Body3D highlight={active.organ} fit={1.08} sex={sex} /></div>
          <div className="jt-trail" aria-label="Journey path">
            {journey.map((s, i) => (
              <span key={i} className={i === step ? 'on' : ''} onClick={() => pick(i)}>{ORGAN_LABELS[s.organ]}</span>
            ))}
          </div>
        </section>

        <div className="jt-col">
        <section className="panel" aria-label="Journey steps">
          <div className="jt-steps-head">
            <div className="lbl">The drug's path</div>
            <button type="button" className={`jt-ctl${playing ? ' on' : ''}`} onClick={() => setPlaying((p) => !p)}>
              {playing ? 'Pause' : 'Play'}
            </button>
          </div>
          {journey.map((s, i) => (
            <button type="button" key={i} className={`jt-step${i === step ? ' on' : ''}`}
                    aria-current={i === step} onClick={() => pick(i)}>
              <span className="jt-idx">{i + 1}</span>
              <span className="jt-step-body">
                <span className="jt-step-top">
                  <span className="jt-step-name">{s.step}</span>
                  <span className="jt-step-organ">{ORGAN_LABELS[s.organ]}</span>
                </span>
                <span className="jt-step-text">{s.text}</span>
              </span>
            </button>
          ))}
        </section>
        <section className="panel jt-ctls" aria-label="Dose controls">
          <div>
            <div className="jt-ctl-head">
              <label htmlFor="jt-dose" className="lbl">Dose</label>
              <span><span className="mono">{doseMg}</span><small>mg</small></span>
            </div>
            <input id="jt-dose" className="jt-range" type="range" min={dose.min} max={dose.max} step="1"
                   value={doseMg} onChange={(e) => setDoseMg(Number(e.target.value))} />
            <div className="jt-minmax mono"><span>{dose.min} mg</span><span>label range</span><span>{dose.max} mg</span></div>
          </div>
          <div>
            <div className="lbl" id="jt-ivl">Dosing interval</div>
            <div className="jt-chips" role="group" aria-labelledby="jt-ivl">
              {dose.intervals_h.map((h) => (
                <button type="button" key={h} className={`jt-chip${h === intervalH ? ' on' : ''}`}
                        aria-pressed={h === intervalH} onClick={() => setIntervalH(h)}>every {h} h</button>
              ))}
            </div>
          </div>
          <div>
            <div className="jt-ctl-head">
              <label htmlFor="jt-wt" className="lbl">Body weight</label>
              <span><span className="mono">{perKg ? weightKg : 70}</span><small>kg</small></span>
            </div>
            <input id="jt-wt" className="jt-range" type="range" min="40" max="150" step="1"
                   value={perKg ? weightKg : 70} disabled={!perKg}
                   onChange={(e) => setWeightKg(Number(e.target.value))} />
            <div className="jt-wtnote">
              {perKg ? 'Shows how body size changes the curve. Not a dosing tool.'
                : "Fixed: this drug's label doesn't scale with weight."}
            </div>
          </div>
          <p className="jt-warn">Population-average estimate for learning only. Not a dosing tool and not medical advice. Never change a dose without your doctor.</p>
        </section>
        </div>
      </div>
    </div>
  )
}
