import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { GHOST_COLOR, HIGHLIGHT_COLOR, LEVEL_COLORS, LEVEL_OPACITY } from '../lib/organs.js'

const ANATOMY_BASE = `${import.meta.env.BASE_URL}anatomy`

let atlasPromise = null
function loadAtlas() {
  if (!atlasPromise) {
    atlasPromise = Promise.all([
      fetch(`${ANATOMY_BASE}/organs.json`).then((r) => r.json()),
      fetch(`${ANATOMY_BASE}/organs.bin.gz`).then((r) => r.arrayBuffer()),
    ]).then(async ([manifest, payload]) => {
      // Some static hosts (e.g. Vite's dev server) see the .gz extension and
      // set Content-Encoding: gzip, so fetch() already decompressed it; others
      // (e.g. GitHub Pages) serve the raw gzip bytes as an opaque binary.
      // Detect which happened from the gzip magic bytes rather than assuming.
      const signature = new Uint8Array(payload, 0, 2)
      const isGzip = signature[0] === 0x1f && signature[1] === 0x8b
      const buffer = isGzip
        ? await new Response(new Blob([payload]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer()
        : payload
      return { manifest, buffer }
    })
  }
  return atlasPromise
}

function styleFor(organ, { bodyMap, selected, highlight }) {
  if (highlight === organ) return { color: HIGHLIGHT_COLOR, opacity: 0.95, emissive: 1.1 }
  const entry = bodyMap[organ]
  if (!entry || !LEVEL_COLORS[entry.level]) {
    return { color: GHOST_COLOR, opacity: organ === 'skin' ? 0.1 : 0.06, emissive: 0.05 }
  }
  let opacity = LEVEL_OPACITY[entry.level]
  if (entry.basis === 'rna') opacity *= 0.55
  return { color: LEVEL_COLORS[entry.level], opacity, emissive: selected === organ ? 0.5 : 0.2 }
}

export default function Body3D({ bodyMap = {}, selected, highlight, onSelect }) {
  const hostRef = useRef(null)
  const propsRef = useRef({ bodyMap, selected, highlight, onSelect })
  propsRef.current = { bodyMap, selected, highlight, onSelect }
  const meshesRef = useRef({})
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    const host = hostRef.current
    let disposed = false
    let renderer, camera, controls, frame
    const scene = new THREE.Scene()
    const geometries = []
    const materials = []

    loadAtlas()
      .then(({ manifest, buffer }) => {
        if (disposed || !host) return

        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
        renderer.setClearColor(0x000000, 0)
        renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
        renderer.setSize(host.clientWidth, host.clientHeight)
        host.appendChild(renderer.domElement)

        camera = new THREE.PerspectiveCamera(35, host.clientWidth / host.clientHeight, 0.01, 100)
        controls = new OrbitControls(camera, renderer.domElement)
        controls.enableDamping = true
        controls.dampingFactor = 0.08
        controls.minDistance = 0.3
        controls.maxDistance = 6

        const [min, max] = manifest.bounds
        const center = new THREE.Vector3((min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2)
        const height = max[1] - min[1]
        const distance = (height / 2) / Math.tan(THREE.MathUtils.degToRad(17.5)) * 1.5
        camera.position.set(center.x, center.y, center.z + distance)
        controls.target.copy(center)
        controls.update()

        scene.add(new THREE.AmbientLight(0x6fa8c0, 1.2))
        const key = new THREE.DirectionalLight(0xbfe8f5, 1.4)
        key.position.set(-2, 4, 3)
        scene.add(key)
        const rim = new THREE.DirectionalLight(0x22d3ee, 0.9)
        rim.position.set(2, 1, -3)
        scene.add(rim)

        const raycastMeshes = []
        for (const [organ, part] of Object.entries(manifest.organs)) {
          const geo = new THREE.BufferGeometry()
          geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(buffer, part.positions, part.vertexCount * 3), 3))
          geo.setAttribute('normal', new THREE.BufferAttribute(new Int16Array(buffer, part.normals, part.vertexCount * 3), 3, true))
          geo.setIndex(new THREE.BufferAttribute(new Uint32Array(buffer, part.indices, part.indexCount), 1))
          geometries.push(geo)

          const style = styleFor(organ, propsRef.current)
          const material = new THREE.MeshStandardMaterial({
            color: style.color, transparent: true, opacity: style.opacity,
            emissive: style.color, emissiveIntensity: style.emissive,
            roughness: 0.55, metalness: 0.05, side: THREE.DoubleSide, depthWrite: false,
          })
          materials.push(material)

          const mesh = new THREE.Mesh(geo, material)
          mesh.renderOrder = organ === 'skin' ? 0 : 1
          scene.add(mesh)
          meshesRef.current[organ] = mesh
          raycastMeshes.push(mesh)
        }

        const resize = () => {
          if (!host) return
          camera.aspect = host.clientWidth / host.clientHeight
          camera.updateProjectionMatrix()
          renderer.setSize(host.clientWidth, host.clientHeight)
        }
        const observer = new ResizeObserver(resize)
        observer.observe(host)

        const raycaster = new THREE.Raycaster()
        const pointer = new THREE.Vector2()
        let downAt = null
        const onDown = (e) => { downAt = [e.clientX, e.clientY] }
        const onUp = (e) => {
          if (!downAt) return
          const moved = Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1])
          downAt = null
          if (moved > 6 || !propsRef.current.onSelect) return
          const rect = renderer.domElement.getBoundingClientRect()
          pointer.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1)
          raycaster.setFromCamera(pointer, camera)
          const hits = raycaster.intersectObjects(raycastMeshes, false)
          const hit = hits.find((h) => h.object !== meshesRef.current.skin) ?? hits[0]
          if (hit) {
            const organ = Object.entries(meshesRef.current).find(([, m]) => m === hit.object)?.[0]
            if (organ) propsRef.current.onSelect(organ)
          }
        }
        renderer.domElement.addEventListener('pointerdown', onDown)
        renderer.domElement.addEventListener('pointerup', onUp)

        const animate = () => {
          if (disposed) return
          frame = requestAnimationFrame(animate)
          controls.update()
          renderer.render(scene, camera)
        }
        animate()

        setStatus('ready')

        meshesRef.current.__cleanup = () => {
          observer.disconnect()
          renderer.domElement.removeEventListener('pointerdown', onDown)
          renderer.domElement.removeEventListener('pointerup', onUp)
        }
      })
      .catch((err) => { console.error('Body3D failed to load:', err); if (!disposed) setStatus('error') })

    return () => {
      disposed = true
      cancelAnimationFrame(frame)
      meshesRef.current.__cleanup?.()
      controls?.dispose()
      geometries.forEach((g) => g.dispose())
      materials.forEach((m) => m.dispose())
      if (renderer) {
        renderer.dispose()
        renderer.domElement.remove()
      }
      meshesRef.current = {}
    }
  }, [])

  // Recolor in place on prop changes -- no scene/geometry rebuild.
  useEffect(() => {
    for (const [organ, mesh] of Object.entries(meshesRef.current)) {
      if (organ === '__cleanup' || !mesh.material) continue
      const style = styleFor(organ, { bodyMap, selected, highlight })
      mesh.material.color.set(style.color)
      mesh.material.emissive.set(style.color)
      mesh.material.emissiveIntensity = style.emissive
      mesh.material.opacity = style.opacity
    }
  }, [bodyMap, selected, highlight])

  return (
    <div>
      <div className="body3d-viewer" ref={hostRef} />
      {status === 'loading' && <p className="loading-state">Loading 3D body…</p>}
      {status === 'error' && <p className="error-banner">Couldn't load the 3D body right now.</p>}
      {status === 'ready' && <p className="muted small">Drag to rotate, scroll to zoom.</p>}
    </div>
  )
}

export function BodyLegend() {
  return (
    <div className="legend">
      {Object.entries(LEVEL_COLORS).map(([level, color]) => (
        <span key={level}><i style={{ background: color }} />{level}</span>
      ))}
      <span><i style={{ background: LEVEL_COLORS.high, opacity: 0.5 }} />based on RNA (no protein data)</span>
    </div>
  )
}
