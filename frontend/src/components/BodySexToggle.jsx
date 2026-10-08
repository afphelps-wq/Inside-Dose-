import { SEXES, useBodySex } from '../lib/bodySex.js'

// Male / female anatomy switch for the 3D body.
export default function BodySexToggle() {
  const [sex, setSex] = useBodySex()
  return (
    <div className="sex-toggle" role="group" aria-label="Body model">
      {SEXES.map((s) => (
        <button key={s} type="button" className={s === sex ? 'on' : ''} aria-pressed={s === sex} onClick={() => setSex(s)}>
          {s === 'male' ? 'Male' : 'Female'}
        </button>
      ))}
    </div>
  )
}
