import { useSyncExternalStore } from 'react'

const KEY = 'inside-dose:body-sex'
export const SEXES = ['male', 'female']

function load() {
  try {
    return localStorage.getItem(KEY) === 'female' ? 'female' : 'male'
  } catch {
    return 'male'
  }
}

// Which anatomy the 3D body shows. Shared, so the Journey and Targets & Body tabs stay in step.
let current = load()
const listeners = new Set()

export function setBodySex(sex) {
  if (!SEXES.includes(sex) || sex === current) return
  current = sex
  try { localStorage.setItem(KEY, sex) } catch { /* session-only */ }
  listeners.forEach((listener) => listener())
}

const subscribe = (listener) => {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function useBodySex() {
  return [useSyncExternalStore(subscribe, () => current), setBodySex]
}
