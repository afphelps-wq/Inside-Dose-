const W = 560
const H = 260
const PAD = { left: 56, right: 16, top: 16, bottom: 40 }

function niceTicks(max, count = 5) {
  const raw = max / count
  const magnitude = 10 ** Math.floor(Math.log10(raw))
  const step = [1, 2, 5, 10].map((m) => m * magnitude).find((s) => s >= raw)
  const ticks = []
  for (let v = 0; v <= max + 1e-9; v += step) ticks.push(Number(v.toFixed(10)))
  return ticks
}

export default function ConcentrationChart({ points, windowH }) {
  const maxC = Math.max(...points.map((p) => p.c)) * 1.1 || 1
  const x = (t) => PAD.left + (t / windowH) * (W - PAD.left - PAD.right)
  const y = (c) => H - PAD.bottom - (c / maxC) * (H - PAD.top - PAD.bottom)
  const path = points.map((p, i) => `${i ? 'L' : 'M'}${x(p.t).toFixed(1)},${y(p.c).toFixed(1)}`).join('')
  const area = `${path}L${x(windowH)},${y(0)}L${x(0)},${y(0)}Z`

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart" role="img"
         aria-label="Estimated blood level over time">
      {niceTicks(maxC).map((c) => (
        <g key={c}>
          <line x1={PAD.left} x2={W - PAD.right} y1={y(c)} y2={y(c)} className="grid" />
          <text x={PAD.left - 8} y={y(c) + 4} textAnchor="end">{c}</text>
        </g>
      ))}
      {niceTicks(windowH, 6).map((t) => (
        <text key={t} x={x(t)} y={H - PAD.bottom + 18} textAnchor="middle">{t}</text>
      ))}
      <path d={area} className="curve-area" />
      <path d={path} className="curve" />
      <text x={(W + PAD.left) / 2} y={H - 4} textAnchor="middle" className="axis-label">Hours after first dose</text>
      <text x={14} y={H / 2} textAnchor="middle" className="axis-label"
            transform={`rotate(-90 14 ${H / 2})`}>mg/L</text>
    </svg>
  )
}
