import { useEffect, useMemo, useState } from 'react'
import { concentrationCurve } from '../../lib/pk.js'
import BodyMap, { ORGAN_LABELS } from '../BodyMap.jsx'
import ConcentrationChart from '../ConcentrationChart.jsx'

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
  const active = journey[step]

  return (
    <div className="stack">
      <div className="tab-grid">
        <div className="card center">
          <BodyMap highlight={active.organ} />
        </div>
        <div className="card">
          <div className="row">
            <h3>The drug's journey</h3>
            <button className="ghost" onClick={() => setPlaying((p) => !p)}>{playing ? 'Pause' : 'Play'}</button>
          </div>
          <ol className="journey">
            {journey.map((s, i) => (
              <li key={i} className={i === step ? 'active' : ''} onClick={() => { setStep(i); setPlaying(false) }}>
                <span className="step-name">{s.step}</span>
                <span className="muted"> · {ORGAN_LABELS[s.organ]}</span>
                <p>{s.text}</p>
              </li>
            ))}
          </ol>
        </div>
      </div>

      <div className="card">
        <h3>Estimated blood level (population average)</h3>
        <ConcentrationChart points={curve.points} windowH={curve.windowH} />
        <div className="sliders">
          <label>
            Dose: <strong>{doseMg} mg</strong>
            <input type="range" min={dose.min} max={dose.max} step="1"
                   value={doseMg} onChange={(e) => setDoseMg(Number(e.target.value))} />
          </label>
          <label>
            Every
            <select value={intervalH} onChange={(e) => setIntervalH(Number(e.target.value))}>
              {dose.intervals_h.map((h) => <option key={h} value={h}>{h} hours</option>)}
            </select>
          </label>
          <label className={perKg ? '' : 'disabled'}>
            Body weight: <strong>{perKg ? weightKg : 70} kg</strong>
            <input type="range" min="40" max="150" value={perKg ? weightKg : 70} disabled={!perKg}
                   onChange={(e) => setWeightKg(Number(e.target.value))} />
            <small>
              {perKg ? 'Shows how body size changes the curve. Not a dosing tool.'
                : "Fixed: this drug's label doesn't scale with weight."}
            </small>
          </label>
        </div>
        <p className="slider-note">Educational, not medical advice. Never change a dose without your doctor.</p>
      </div>
    </div>
  )
}
