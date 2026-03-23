export default function Layout({ tab, setTab, children }) {
  return (
    <div>
      <header className="app-header">
        <span className="app-title">CP Project</span>
        <span className="login-placeholder">login</span>
      </header>
      <nav className="tab-strip">
        <button
          type="button"
          className={`tab-btn${tab === 'jobs' ? ' active' : ''}`}
          onClick={() => setTab('jobs')}
        >
          Jobs
        </button>
        <button
          type="button"
          className={`tab-btn${tab === 'employees' ? ' active' : ''}`}
          onClick={() => setTab('employees')}
        >
          Employees
        </button>
        <button
          type="button"
          className={`tab-btn${tab === 'equipment' ? ' active' : ''}`}
          onClick={() => setTab('equipment')}
        >
          Equipment
        </button>
      </nav>
      <main>{children}</main>
    </div>
  )
}
