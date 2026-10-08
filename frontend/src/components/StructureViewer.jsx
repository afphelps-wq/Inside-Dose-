import { useEffect, useRef, useState } from 'react'
import { getTargetStructures } from '../api/client.js'
import { loadMolstar } from '../lib/molstarLoader.js'
import { useTheme } from '../lib/theme.jsx'

const BACKGROUNDS = { dark: 0x060d1a, light: 0xeaf3ff } // matches --viewer-bg
const setBackground = (viewer, theme) => {
  try { viewer?.plugin.canvas3d?.setProps({ renderer: { backgroundColor: BACKGROUNDS[theme] } }) } catch { /* cosmetic only */ }
}

const VIEWER_OPTIONS = {
  layoutIsExpanded: false,
  layoutShowControls: false,
  layoutShowRemoteState: false,
  layoutShowSequence: false,
  layoutShowLog: false,
  layoutShowLeftPanel: false,
  viewportShowExpand: false,
  viewportShowSelectionMode: false,
  viewportShowAnimation: false,
}

// Targets tab's "3D drug-in-target view when a PDB structure exists" (spec
// §4, §6.3). Picks the best solved structure for a target -- one with this
// drug actually bound, if RCSB has one, else just the target alone -- and
// renders it with Mol* (see frontend/src/assets/CREDITS.md).
export default function StructureViewer({ uniprot, rxcui }) {
  const containerRef = useRef(null)
  const viewerRef = useRef(null)
  const { theme } = useTheme()
  const themeRef = useRef(theme)
  themeRef.current = theme
  const [structure, setStructure] = useState(undefined) // undefined = loading, null = none found
  const [error, setError] = useState(null)
  const [retryNonce, setRetryNonce] = useState(0)

  useEffect(() => {
    setStructure(undefined)
    setError(null)
    const controller = new AbortController()
    getTargetStructures(uniprot, rxcui, { signal: controller.signal })
      .then((structures) => {
        setStructure(structures.find((s) => s.has_this_drug) ?? structures[0] ?? null)
      })
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message) })
    return () => controller.abort()
  }, [uniprot, rxcui, retryNonce])

  useEffect(() => {
    if (!structure || !containerRef.current) return
    let viewer = null
    let cancelled = false
    const container = containerRef.current
    // Mol*'s own "Toggle Full Screen" only expands the viewer inside the page layout.
    // Swallow it and fullscreen just this viewer through the browser's Fullscreen API.
    // If the browser refuses real fullscreen, fall back to covering the whole window with just this viewer.
    const refit = () => window.dispatchEvent(new Event('resize'))
    const setPseudo = (on) => {
      container.classList.toggle('structure-viewer-expanded', on)
      document.body.classList.toggle('viewer-expanded', on)
      refit()
    }
    const onFullscreenClick = (event) => {
      if (!event.target.closest?.('button[title="Toggle Full Screen"]')) return
      event.preventDefault()
      event.stopPropagation()
      if (document.fullscreenElement === container) document.exitFullscreen()
      else if (container.classList.contains('structure-viewer-expanded')) setPseudo(false)
      else (container.requestFullscreen?.() ?? Promise.reject()).catch(() => setPseudo(true))
    }
    const onKey = (event) => {
      if (event.key === 'Escape' && container.classList.contains('structure-viewer-expanded')) setPseudo(false)
    }
    document.addEventListener('keydown', onKey)
    const onFsChange = refit
    document.addEventListener('fullscreenchange', onFsChange)
    container.addEventListener('click', onFullscreenClick, true)
    loadMolstar()
      .then((molstar) => {
        if (cancelled || !containerRef.current) return
        return molstar.Viewer.create(containerRef.current, VIEWER_OPTIONS)
      })
      .then((createdViewer) => {
        if (cancelled || !createdViewer) return
        viewer = createdViewer
        viewerRef.current = viewer
        // Match the app theme instead of Mol*'s default white background.
        setBackground(viewer, themeRef.current)
        return viewer.loadPdb(structure.pdb_id)
      })
      .catch((err) => { if (!cancelled) setError(err.message) })
    return () => {
      cancelled = true
      container.removeEventListener('click', onFullscreenClick, true)
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('fullscreenchange', onFsChange)
      setPseudo(false)
      if (document.fullscreenElement === container) document.exitFullscreen()
      viewerRef.current = null
      viewer?.plugin?.dispose?.()
    }
  }, [structure])

  useEffect(() => { setBackground(viewerRef.current, theme) }, [theme])

  if (error) {
    return (
      <p className="error-banner">
        Couldn't load the 3D structure: {error}{' '}
        <button className="ghost" onClick={() => setRetryNonce((n) => n + 1)}>Retry</button>
      </p>
    )
  }
  if (structure === undefined) return <p className="loading-state">Checking for a solved structure…</p>
  if (structure === null) return null

  return (
    <div className="structure-viewer-block">
      <div className="structure-viewer" ref={containerRef} />
      <p className="muted small">
        PDB {structure.pdb_id} &mdash; {structure.title}
        {structure.has_this_drug ? ' (this drug bound)' : ' (target structure; this drug not shown bound here)'}
      </p>
    </div>
  )
}
