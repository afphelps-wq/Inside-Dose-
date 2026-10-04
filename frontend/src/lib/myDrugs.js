import { useCallback, useState } from 'react'

const KEY = 'inside-dose:my-drugs'
export const MAX_DRUGS = 5

function load() {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY))
    return { list: Array.isArray(saved) ? saved : [], persistent: true }
  } catch {
    return { list: [], persistent: false }
  }
}

// Saved rxcuis, kept in localStorage when available (spec §2.4); session-only otherwise.
export function useMyDrugs() {
  const [{ list, persistent }, setState] = useState(load)

  const save = useCallback((next) => {
    let stored = true
    try {
      localStorage.setItem(KEY, JSON.stringify(next))
    } catch {
      stored = false
    }
    setState({ list: next, persistent: stored })
  }, [])

  const add = (rxcui) => {
    if (!list.includes(rxcui) && list.length < MAX_DRUGS) save([...list, rxcui])
  }
  const remove = (rxcui) => save(list.filter((id) => id !== rxcui))

  return { list, persistent, add, remove, has: (rxcui) => list.includes(rxcui) }
}
