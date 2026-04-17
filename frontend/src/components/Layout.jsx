import { NavLink, Link } from 'react-router-dom'
import cpMark from '../assets/cpmark.svg'

export default function Layout({ children }) {
  return (
    <div>
      <header className="app-header">
        <Link to="/" className="app-title-link">
          <img src={cpMark} alt="CP" className="app-icon" />
          <div className="app-wordmark">
            <div className="app-wordmark-name">CONSTRUCTION COMPANY, INC.</div>
            <div className="app-wordmark-tag">WATER &middot; SEWER &middot; STORM DRAIN</div>
          </div>
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
