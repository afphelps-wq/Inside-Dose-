const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export async function getJson(path, { signal } = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, { signal })
  const body = await response.json().catch(() => null)
  if (!response.ok) {
    const message = body?.error?.message || 'Something went wrong.'
    throw new Error(message)
  }
  return body
}

export function checkHealth({ signal } = {}) {
  return getJson('/health', { signal })
}

export function getCuratedDrugs({ signal } = {}) {
  return getJson('/drugs/curated', { signal })
}

export function searchDrugs(q, { signal } = {}) {
  return getJson(`/search?q=${encodeURIComponent(q)}`, { signal })
}

export function getDrug(rxcui, { signal } = {}) {
  return getJson(`/drugs/${encodeURIComponent(rxcui)}`, { signal })
}

export async function postInteractions(rxcuis, { signal } = {}) {
  const response = await fetch(`${API_BASE_URL}/interactions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rxcuis }),
    signal,
  })
  const body = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(body?.error?.message || 'Something went wrong.')
  }
  return body
}

export async function getStructureSdf(rxcui, { signal } = {}) {
  const response = await fetch(`${API_BASE_URL}/drugs/${encodeURIComponent(rxcui)}/structure.sdf`, { signal })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.error?.message || "Couldn't load the molecule structure right now.")
  }
  return response.text()
}
