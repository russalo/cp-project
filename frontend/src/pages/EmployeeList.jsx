import { useState, useEffect } from 'react'
import { fetchEmployees } from '../services/api'

export default function EmployeeList() {
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showInactive, setShowInactive] = useState(false)

  useEffect(() => {
    let cancelled = false
    fetchEmployees(showInactive)
      .then(data => {
        if (!cancelled) { setEmployees(data); setError(null); setLoading(false) }
      })
      .catch(err => {
        if (!cancelled) { setError(err.message); setLoading(false) }
      })
    return () => { cancelled = true }
  }, [showInactive])

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Employees</h1>
        <div className="page-toolbar">
          <label className="show-inactive-label">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={e => setShowInactive(e.target.checked)}
            />
            Show inactive
          </label>
        </div>
      </div>

      {loading && <div className="loading-state">Loading…</div>}
      {error && <div className="error-state">Error: {error}</div>}

      {!loading && !error && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
              <th>Trade</th>
              <th>Union</th>
              <th>Reg</th>
              <th>OT</th>
              <th>DT</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {employees.length === 0 ? (
              <tr>
                <td colSpan={8} className="rate-unavailable" style={{ textAlign: 'center', padding: '32px' }}>
                  No employees found.
                </td>
              </tr>
            ) : (
              employees.map(emp => (
                <tr key={emp.id}>
                  <td><code>{emp.code}</code></td>
                  <td>{emp.full_name}</td>
                  <td>{emp.trade_name}</td>
                  <td>{emp.union_abbrev}</td>
                  <td className="rate-cell">
                    {emp.rate_available
                      ? `$${emp.rate_reg}`
                      : <span className="rate-unavailable">—</span>}
                  </td>
                  <td className="rate-cell">
                    {emp.rate_available
                      ? `$${emp.rate_ot}`
                      : <span className="rate-unavailable">—</span>}
                  </td>
                  <td className="rate-cell">
                    {emp.rate_available
                      ? `$${emp.rate_dt}`
                      : <span className="rate-unavailable">—</span>}
                  </td>
                  <td>
                    <span className={emp.active ? 'badge badge-active' : 'badge badge-inactive'}>
                      {emp.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}
    </div>
  )
}
