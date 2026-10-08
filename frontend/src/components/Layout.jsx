import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import ServerStatus from './ServerStatus.jsx'
import ThemeToggle from './ThemeToggle.jsx'
import { MAX_DRUGS, useMyDrugs } from '../lib/myDrugs.js'

const scrollToId = (id) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })

export default function Layout() {
  const isHome = useLocation().pathname === '/'
  const myDrugs = useMyDrugs()

  return (
    <div className="layout">
      <header className="site-header">
        <Link to="/" className="brand">
          <svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true">
            <rect x="4" y="9" width="22" height="12" rx="6" transform="rotate(-35 15 15)" className="brand-pill" />
            <path d="M15 6.5 L15 23.5" transform="rotate(-35 15 15)" className="brand-line" />
          </svg>
          <span>Inside Dose</span>
        </Link>
        <nav aria-label="Main">
          {isHome ? (
            <>
              <button type="button" className="nav-btn" onClick={() => scrollToId('gallery')}>Curated drugs</button>
              <button type="button" className="nav-btn" onClick={() => scrollToId('how')}>How it works</button>
            </>
          ) : (
            <NavLink to="/" end>Home</NavLink>
          )}
          <NavLink to="/my-drugs">
            My Drugs <span className="nav-count">{myDrugs.list.length}/{MAX_DRUGS}</span>
          </NavLink>
          <ThemeToggle />
        </nav>
      </header>
      {!isHome && (
        <>
          <div className="disclaimer" role="note">
            Educational, not medical advice.
          </div>
          <ServerStatus />
        </>
      )}
      <main>
        <Outlet />
      </main>
    </div>
  )
}
