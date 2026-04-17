import { NavLink, Link } from 'react-router-dom'

export default function Layout({ children }) {
  return (
    <div>
      <header className="app-header">
        <Link to="/" className="app-title-link">
          <span className="app-title">CP Project</span>
        </Link>
        <span className="login-placeholder">login</span>
      </header>
      <nav className="tab-strip">
        <NavLink to="/jobs" className={navCls}>Jobs</NavLink>
        <NavLink to="/employees" className={navCls}>Employees</NavLink>
        <NavLink to="/equipment" className={navCls}>Equipment</NavLink>
      </nav>
      <main>{children}</main>
    </div>
  )
}

function navCls({ isActive }) {
  return `tab-btn${isActive ? ' active' : ''}`
}
