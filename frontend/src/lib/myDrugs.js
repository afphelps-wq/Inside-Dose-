import { useSyncExternalStore } from 'react'

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

// One shared store, so every component (header count, drug page, My Drugs) sees the same list.
let state = load()
const listeners = new Set()

function save(next) {
  let stored = true
  try {
    localStorage.setItem(KEY, JSON.stringify(next))
  } catch {
    stored = false
  }
  state = { list: next, persistent: stored }
  listeners.forEach((listener) => listener())
}

const subscribe = (listener) => {
  listeners.add(listener)
  return () => listeners.delete(listener)
}
const getSnapshot = () => state

// Saved rxcuis, kept in localStorage when available (spec §2.4); session-only otherwise.
export function useMyDrugs() {
  const { list, persistent } = useSyncExternalStore(subscribe, getSnapshot)

  const add = (rxcui) => {
    if (!state.list.includes(rxcui) && state.list.length < MAX_DRUGS) save([...state.list, rxcui])
  }
  const remove = (rxcui) => save(state.list.filter((id) => id !== rxcui))

  return { list, persistent, add, remove, has: (rxcui) => list.includes(rxcui) }
}
