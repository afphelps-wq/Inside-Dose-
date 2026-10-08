import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

const KEY = 'inside-dose:theme'

function load() {
  try {
    return localStorage.getItem(KEY) === 'dark' ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

const ThemeContext = createContext({ theme: 'light', toggle: () => {} })

// Site-wide light/dark theme. Light by default; the choice is remembered in localStorage when
// available. The theme lives on <html data-theme>, which styles.css keys all its tokens off.
export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(load)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  const toggle = useCallback(() => {
    setTheme((current) => {
      const next = current === 'dark' ? 'light' : 'dark'
      try { localStorage.setItem(KEY, next) } catch { /* session-only */ }
      return next
    })
  }, [])

  const value = useMemo(() => ({ theme, toggle }), [theme, toggle])
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export const useTheme = () => useContext(ThemeContext)
