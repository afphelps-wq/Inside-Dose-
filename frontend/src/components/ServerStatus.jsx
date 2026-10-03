import { useEffect, useState } from 'react'
import { checkHealth } from '../api/client.js'

const WAKING_DELAY_MS = 3000
const RETRY_DELAY_MS = 5000

// Pings /health until the Render server answers. Shows "Waking up the server…"
// only when the first answer takes longer than 3 s (spec §3.1, §7).
export default function ServerStatus() {
  const [status, setStatus] = useState('checking')

  useEffect(() => {
    let cancelled = false
    let retryTimer
    const controller = new AbortController()
    const wakingTimer = setTimeout(() => {
      if (!cancelled) setStatus('waking')
    }, WAKING_DELAY_MS)

    async function ping() {
      try {
        await checkHealth({ signal: controller.signal })
        if (cancelled) return
        clearTimeout(wakingTimer)
        setStatus('ready')
      } catch {
        if (cancelled) return
        retryTimer = setTimeout(ping, RETRY_DELAY_MS)
      }
    }
    ping()

    return () => {
      cancelled = true
      controller.abort()
      clearTimeout(wakingTimer)
      clearTimeout(retryTimer)
    }
  }, [])

  if (status === 'waking') {
    return (
      <div className="server-status waking" role="status">
        <span className="spinner" aria-hidden="true" /> Waking up the server…
      </div>
    )
  }
  if (status === 'ready') {
    return (
      <div className="server-status ready" role="status">
        Server connected
      </div>
    )
  }
  return null
}
