import { describe, expect, test } from 'vitest'
import { concentrationCurve, solveKa } from './pk.js'

// Expected values below are independently computed (Python, not this code) from
// the real curated PK model values (spec §6.2) for two drugs, as a hand-calculation
// cross-check:
//   metoprolol: bioavailability 0.5, half_life 3.5 h, vd 4.4 L/kg, tmax 1.75 h
//   apixaban:   bioavailability 0.5, half_life 12 h,  vd 21 L (not per kg), tmax 3.5 h

function singleDoseCurve(drug) {
  return concentrationCurve({
    doseMg: drug.dose,
    intervalH: 1e6, // effectively single-dose: only the t=0 dose contributes
    weightKg: drug.weightKg,
    pk: {
      bioavailability: drug.bioavailability,
      half_life: drug.half_life,
      vd: drug.vd,
      vd_unit: drug.vd_unit,
      tmax: drug.tmax,
    },
  })
}

function concentrationAt(curve, t) {
  // sample points land on multiples of 0.1h; pick the closest one
  const point = curve.points.reduce((best, p) => (Math.abs(p.t - t) < Math.abs(best.t - t) ? p : best))
  return point.c
}

describe('solveKa', () => {
  test('recovers a known ka from its own tmax (round trip)', () => {
    const ke = 0.2
    const ka = 1.0
    const tmax = Math.log(ka / ke) / (ka - ke)
    expect(solveKa(ke, tmax)).toBeCloseTo(ka, 5)
  })

  test('falls back to ka = 10 x ke when tmax has no solution', () => {
    const ke = 0.2
    expect(solveKa(ke, 1 / ke)).toBeCloseTo(10 * ke, 9) // tmax at the ka->ke limit: no solution
    expect(solveKa(ke, 100)).toBeCloseTo(10 * ke, 9) // tmax far too large: no solution
  })
})

describe('concentrationCurve (hand-calculated cross-check)', () => {
  const metoprolol = {
    dose: 50, weightKg: 70, bioavailability: 0.5, half_life: 3.5, vd: 4.4, vd_unit: 'L/kg', tmax: 1.75,
  }
  const apixaban = {
    dose: 5, weightKg: 70, bioavailability: 0.5, half_life: 12, vd: 21, vd_unit: 'L', tmax: 3.5,
  }

  test('metoprolol: concentration at tmax and at 1 h matches hand calculation', () => {
    const curve = singleDoseCurve(metoprolol)
    expect(concentrationAt(curve, 1.75)).toBeCloseTo(0.05739503094046653, 4)
    expect(concentrationAt(curve, 1.0)).toBeCloseTo(0.05151900167007882, 4)
  })

  test('apixaban: concentration at tmax and at 1 h matches hand calculation (Vd not per kg)', () => {
    const curve = singleDoseCurve(apixaban)
    expect(concentrationAt(curve, 3.5)).toBeCloseTo(0.09725687221673213, 4)
    expect(concentrationAt(curve, 1.0)).toBeCloseTo(0.06414481547751426, 4)
  })

  test('time window is max(24h, 5 x half_life) capped at 7 days, sampled every 0.1h', () => {
    expect(singleDoseCurve(metoprolol).windowH).toBe(24) // 5 x 3.5 = 17.5 < 24
    expect(singleDoseCurve(apixaban).windowH).toBe(60) // 5 x 12 = 60
    const longHalfLife = { ...metoprolol, half_life: 100 } // 5 x 100 = 500 > 168
    expect(singleDoseCurve(longHalfLife).windowH).toBe(168)
    const curve = singleDoseCurve(apixaban)
    expect(curve.points.length).toBe(Math.round(60 / 0.1) + 1)
  })

  test('repeated dosing superposes shifted single-dose curves', () => {
    const intervalH = 12
    const repeated = concentrationCurve({
      doseMg: metoprolol.dose, intervalH, weightKg: metoprolol.weightKg,
      pk: {
        bioavailability: metoprolol.bioavailability, half_life: metoprolol.half_life,
        vd: metoprolol.vd, vd_unit: metoprolol.vd_unit, tmax: metoprolol.tmax,
      },
    })
    const single = singleDoseCurve(metoprolol)
    // Just after the second dose, level should exceed the single-dose curve at the same clock time.
    const t = intervalH + 1.75
    expect(concentrationAt(repeated, t)).toBeGreaterThan(concentrationAt(single, t))
  })
})
