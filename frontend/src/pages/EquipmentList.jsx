import { useState, useEffect } from 'react'
import { fetchEquipment } from '../services/api'

export default function EquipmentList() {
  const [equipment, setEquipment] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showInactive, setShowInactive] = useState(false)

  useEffect(() => {
    let cancelled = false
    fetchEquipment(showInactive)
      .then(data => {
        if (!cancelled) { setEquipment(data); setError(null); setLoading(false) }
      })
      .catch(err => {
        if (!cancelled) { setError(err.message); setLoading(false) }
      })
    return () => { cancelled = true }
  }, [showInactive])

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Equipment</h1>
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
              <th>Name</th>
              <th>Class</th>
              <th>Make · Model</th>
              <th>Oper</th>
              <th>Stby</th>
              <th>OT adder</th>
              <th>Unit</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {equipment.length === 0 ? (
              <tr>
                <td colSpan={8} className="rate-unavailable" style={{ textAlign: 'center', padding: '32px' }}>
                  No equipment found.
                </td>
              </tr>
            ) : (
              equipment.map(eq => (
                <tr key={eq.id}>
                  <td>{eq.name}</td>
                  <td>
                    {eq.rate_available
                      ? <><code>{eq.class_code}</code> {eq.class_desc}</>
                      : <span className="rate-unavailable">—</span>}
                  </td>
                  <td>
                    {eq.rate_available
                      ? `${eq.make_desc} · ${eq.model_desc}`
                      : <span className="rate-unavailable">—</span>}
                  </td>
                  <td className="rate-cell">
                    {eq.rate_available
                      ? `$${eq.rental_rate}`
                      : <span className="rate-unavailable">—</span>}
                  </td>
                  <td className="rate-cell">
                    {eq.rate_available
                      ? `$${eq.rw_delay_rate}`
                      : <span className="rate-unavailable">—</span>}
                  </td>
                  <td className="rate-cell">
                    {eq.rate_available
                      ? `+$${eq.overtime_rate}`
                      : <span className="rate-unavailable">—</span>}
                  </td>
                  <td>
                    {eq.rate_available
                      ? eq.unit
                      : <span className="rate-unavailable">—</span>}
                  </td>
                  <td>
                    <span className={eq.active ? 'badge badge-active' : 'badge badge-inactive'}>
                      {eq.active ? 'Active' : 'Inactive'}
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
