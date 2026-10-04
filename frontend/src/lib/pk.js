// One-compartment oral PK model (spec §6.2).

// Solves tmax = ln(ka/ke) / (ka - ke) for ka > ke by bisection.
export function solveKa(ke, tmax) {
  const tmaxAt = (ka) => Math.log(ka / ke) / (ka - ke)
  // As ka -> ke, tmax -> 1/ke; tmax only shrinks as ka grows.
  if (!(tmax > 0) || tmax >= 1 / ke) {
    console.warn('No ka solves this tmax; using ka = 10 x ke')
    return 10 * ke
  }
  let low = ke * (1 + 1e-9)
  let high = ke * 1e6
  for (let i = 0; i < 200; i++) {
    const mid = (low + high) / 2
    if (tmaxAt(mid) > tmax) low = mid
    else high = mid
  }
  return (low + high) / 2
}

export function concentrationCurve({ doseMg, intervalH, weightKg, pk }) {
  const ke = Math.LN2 / pk.half_life
  const ka = solveKa(ke, pk.tmax)
  const V = pk.vd_unit === 'L/kg' ? pk.vd * weightKg : pk.vd
  const F = pk.bioavailability
  const windowH = Math.min(Math.max(24, 5 * pk.half_life), 168)
  const scale = (F * doseMg * ka) / (V * (ka - ke))

  const points = []
  const steps = Math.round(windowH / 0.1)
  for (let i = 0; i <= steps; i++) {
    const t = i * 0.1
    let c = 0
    for (let doseTime = 0; doseTime <= t; doseTime += intervalH) {
      const dt = t - doseTime
      c += scale * (Math.exp(-ke * dt) - Math.exp(-ka * dt))
    }
    points.push({ t, c })
  }
  return { points, windowH }
}
