import { useState, useEffect, useMemo } from 'react'
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
  const [categoryFilter, setCategoryFilter] = useState('')

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

  // Unique, sorted list of categories for the filter dropdown.
  const categories = useMemo(() => {
    const set = new Set(equipment.map(e => e.category).filter(Boolean))
    return [...set].sort()
  }, [equipment])

  // Group rows by category so we can render category banners between them.
  const groups = useMemo(() => {
    const filtered = categoryFilter
      ? equipment.filter(e => e.category === categoryFilter)
      : equipment
    const byCat = new Map()
    for (const eq of filtered) {
      const key = eq.category || '(uncategorized)'
      if (!byCat.has(key)) byCat.set(key, [])
      byCat.get(key).push(eq)
    }
    // Sort groups by category name (matches backend order).
    return [...byCat.entries()].sort((a, b) => a[0].localeCompare(b[0]))
  }, [equipment, categoryFilter])

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Equipment</h1>
        <div className="page-toolbar">
          <label className="show-inactive-label">
            Category:&nbsp;
            <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}>
              <option value="">All ({equipment.length})</option>
              {categories.map(c => (
                <option key={c} value={c}>
                  {c} ({equipment.filter(eq => eq.category === c).length})
                </option>
              ))}
            </select>
          </label>
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

      {!loading && !error && groups.length === 0 && (
        <div className="empty-state">No equipment matches the current filter.</div>
      )}

      {!loading && !error && groups.map(([category, rows]) => (
        <CategoryGroup key={category} category={category} rows={rows} />
      ))}
    </div>
  )
}

function CategoryGroup({ category, rows }) {
  return (
    <>
      <div className="section-banner">
        <h2 className="section-title-inline">{category} ({rows.length})</h2>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Code</th>
            <th>Description</th>
            <th>CT Match</th>
            <th>Oper</th>
            <th>OT</th>
            <th>Stby</th>
            <th>Fuel</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(eq => {
            const rated = hasRates(eq)
            return (
              <tr key={eq.id}>
                <td><code>{eq.name}</code></td>
                <td>{eq.description || <span className="rate-unavailable">—</span>}</td>
                <td>{MATCH_LABEL[eq.ct_match_quality] ?? eq.ct_match_quality}</td>
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
          })}
        </tbody>
      </table>
    </>
  )
}
