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
