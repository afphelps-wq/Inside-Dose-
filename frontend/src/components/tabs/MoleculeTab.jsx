import { useEffect, useRef, useState } from 'react'
import { getStructureSdf } from '../../api/client.js'

export default function MoleculeTab({ rxcui, molecule }) {
  const containerRef = useRef(null)
  const [sdf, setSdf] = useState(null)
  const [error, setError] = useState(null)
  const [retryNonce, setRetryNonce] = useState(0)

  useEffect(() => {
    setSdf(null)
    setError(null)
    const controller = new AbortController()
    getStructureSdf(rxcui, { signal: controller.signal })
      .then(setSdf)
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message) })
    return () => controller.abort()
  }, [rxcui, retryNonce])

  useEffect(() => {
    if (!sdf || !containerRef.current) return
    let cancelled = false
    import('3dmol').then((mod) => {
      if (cancelled || !containerRef.current) return
      const $3Dmol = mod.default ?? mod
      containerRef.current.innerHTML = ''
      const viewer = $3Dmol.createViewer(containerRef.current, { backgroundAlpha: 0 })
      viewer.addModel(sdf, 'sdf')
      viewer.setStyle({}, {
        stick: { radius: 0.15, colorscheme: 'cyanCarbon' },
        sphere: { scale: 0.22, colorscheme: 'cyanCarbon' },
      })
      viewer.zoomTo()
      viewer.render()
    })
    return () => {
      cancelled = true
      if (containerRef.current) containerRef.current.innerHTML = ''
    }
  }, [sdf])

  return (
    <div className="tab-grid">
      <div className="card">
        <div className="molecule-viewer" ref={containerRef} />
        {!sdf && !error && <p className="loading-state">Loading 3D structure…</p>}
        {error && (
          <p className="error-banner">
            Couldn't load the 3D structure: {error}{' '}
            <button className="ghost" onClick={() => setRetryNonce((n) => n + 1)}>Retry</button>
          </p>
        )}
        {sdf && !error && <p className="muted small">Drag to rotate, scroll to zoom.</p>}
      </div>
      <div className="card">
        <h3>Key properties</h3>
        {molecule ? (
          <dl className="props">
            <dt>Formula</dt><dd>{molecule.formula}</dd>
            <dt>Molecular weight</dt><dd>{molecule.weight} g/mol</dd>
          </dl>
        ) : (
          <p className="muted">Couldn't load molecule properties right now.</p>
        )}
      </div>
    </div>
  )
}
