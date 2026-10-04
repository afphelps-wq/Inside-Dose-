import { NavLink, Outlet } from 'react-router-dom'
import ServerStatus from './ServerStatus.jsx'

export default function Layout() {
  return (
    <div className="layout">
      <header className="site-header">
        <NavLink to="/" className="brand">Inside Dose</NavLink>
        <nav>
          <NavLink to="/" end>Home</NavLink>
          <NavLink to="/my-drugs">My Drugs</NavLink>
        </nav>
      </header>
      <div className="disclaimer" role="note">
        Educational, not medical advice.
      </div>
      <div className="demo-banner" role="note">
        Demo data: the drugs shown are fictional and every value is made up.
      </div>
      <ServerStatus />
      <main>
        <Outlet />
      </main>
    </div>
  )
}
