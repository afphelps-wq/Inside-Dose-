import { useTheme } from '../lib/theme.jsx'

export default function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const dark = theme === 'dark'
  const label = dark ? 'Switch to light mode' : 'Switch to dark mode'
  return (
    <button type="button" className="theme-toggle" onClick={toggle} aria-pressed={dark} aria-label={label} title={label}>
      {dark ? (
        <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
          <circle cx="10" cy="10" r="3.6" />
          <path d="M10 1.8v2.2M10 16v2.2M1.8 10H4M16 10h2.2M4.2 4.2l1.6 1.6M14.2 14.2l1.6 1.6M4.2 15.8l1.6-1.6M14.2 5.8l1.6-1.6" />
        </svg>
      ) : (
        <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
          <path d="M16.5 11.6A7 7 0 0 1 8.4 3.5a7 7 0 1 0 8.1 8.1Z" />
        </svg>
      )}
      <span>{dark ? 'Light' : 'Dark'}</span>
    </button>
  )
}
