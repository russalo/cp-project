import { useState, useEffect } from 'react'
import { fetchEquipment } from '../services/api'

const MATCH_LABEL = {
  exact: 'Exact',
  close: 'Close',
  none: 'No match',
  retired: 'CT retired',
  fmv: 'FMV',
}

function hasRates(eq) {
  const n = v => Number(v || 0)
  return n(eq.rate_reg) + n(eq.rate_ot) + n(eq.rate_standby) > 0
}

export default function EquipmentList() {
  const [equipment, setEquipment] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showInactive, setShowInactive] = useState(false)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      if (cancelled) return
      setLoading(true)
      setError(null)
      try {
        const data = await fetchEquipment(showInactive)
        if (!cancelled) setEquipment(data)
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
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
              <th>Code</th>
              <th>CT Match</th>
              <th>Caltrans Class</th>
              <th>Oper</th>
              <th>OT</th>
              <th>Stby</th>
              <th>Fuel</th>
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
              equipment.map(eq => {
                const rated = hasRates(eq)
                return (
                  <tr key={eq.id}>
                    <td><code>{eq.name}</code></td>
                    <td>{MATCH_LABEL[eq.ct_match_quality] ?? eq.ct_match_quality}</td>
                    <td>
                      {eq.ct_class_code
                        ? <><code>{eq.ct_class_code}</code> {eq.ct_class_desc ?? ''}</>
                        : <span className="rate-unavailable">—</span>}
                    </td>
                    <td className="rate-cell">
                      {rated ? `$${eq.rate_reg}` : <span className="rate-unavailable">—</span>}
                    </td>
                    <td className="rate-cell">
                      {rated ? `$${eq.rate_ot}` : <span className="rate-unavailable">—</span>}
                    </td>
                    <td className="rate-cell">
                      {rated ? `$${eq.rate_standby}` : <span className="rate-unavailable">—</span>}
                    </td>
                    <td>{eq.fuel_surcharge_eligible ? 'Yes' : 'No'}</td>
                    <td>
                      <span className={eq.active ? 'badge badge-active' : 'badge badge-inactive'}>
                        {eq.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      )}
    </div>
  )
}
