// Lazy-loads the vendored Mol* viewer bundle (see frontend/src/assets/CREDITS.md)
// exactly once, however many StructureViewer instances mount, and resolves to
// the global `molstar` namespace it defines.
let loadPromise = null

export function loadMolstar() {
  if (loadPromise) return loadPromise

  loadPromise = new Promise((resolve, reject) => {
    if (window.molstar) {
      resolve(window.molstar)
      return
    }

    const vendorBase = `${import.meta.env.BASE_URL}vendor/molstar`

    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = `${vendorBase}/molstar.css`
    document.head.appendChild(link)

    const script = document.createElement('script')
    script.src = `${vendorBase}/molstar.js`
    script.onload = () => resolve(window.molstar)
    script.onerror = () => reject(new Error("Couldn't load the structure viewer right now."))
    document.body.appendChild(script)
  })

  return loadPromise
}
