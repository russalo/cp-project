import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchEwo, fetchJob, fetchWorkDays, patchEwo } from '../services/api'
import EditableField from '../components/EditableField'
import { fmtMoney, fmtPct } from '../lib/format'

const STATUS_LABEL = {
  open: 'Open',
  submitted: 'Submitted',
  approved: 'Approved',
  rejected: 'Rejected',
  sent: 'Sent to GC',
  billed: 'Billed',
}

export default function EwoDetail() {
  const { ewoId } = useParams()
  const [ewo, setEwo] = useState(null)
  const [job, setJob] = useState(null)
  const [workDays, setWorkDays] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const ewoData = await fetchEwo(ewoId)
        if (cancelled) return
        setEwo(ewoData)
        const [jobData, wdData] = await Promise.all([
          fetchJob(ewoData.job),
          fetchWorkDays({ ewo: ewoData.id }),
        ])
        if (cancelled) return
        setJob(jobData)
        setWorkDays(wdData || [])
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [ewoId])

  if (loading) return <div className="page"><div className="loading-state">Loading…</div></div>
  if (error) return <div className="page"><div className="error-state">Error: {error}</div></div>
  if (!ewo) return <div className="page"><div className="error-state">EWO not found.</div></div>

  const locked = !['open', 'rejected'].includes(ewo.status)

  return (
    <div className="page">
      <div className="breadcrumbs">
        <Link to="/jobs">Jobs</Link>
        <span className="breadcrumb-sep">/</span>
        {job ? <Link to={`/jobs/${job.id}`}>{job.job_number}</Link> : '…'}
        <span className="breadcrumb-sep">/</span>
        <span>{ewo.ewo_number}</span>
      </div>

      <div className="page-header">
        <h1 className="page-title">
          <code>{ewo.ewo_number}</code>
          <span className={`badge badge-status-${ewo.status}`} style={{ marginLeft: 12 }}>
            {STATUS_LABEL[ewo.status] || ewo.status}
          </span>
        </h1>
        <div className="page-toolbar">
          {!locked && (
            <Link to={`/ewos/${ewo.id}/workdays/new`} className="btn btn-primary">+ New WorkDay</Link>
          )}
        </div>
      </div>

      <section className="detail-card">
        <dl className="detail-grid">
          <dt>Type</dt>
          <dd>{ewo.ewo_type === 'tm' ? 'Time & Materials' : 'Change Order'}</dd>

          <dt>Description</dt>
          <dd>
            <EditableField
              value={ewo.description}
              locked={locked}
              multiline
              placeholder="(add a description)"
              onSave={(v) => patchEwo(ewo.id, { description: v }).then(setEwo)}
            />
          </dd>

          <dt>Labor OH&P</dt> <dd>{fmtPct(ewo.labor_ohp_pct)}</dd>
          <dt>Equip/Mat OH&P</dt> <dd>{fmtPct(ewo.equip_mat_ohp_pct)}</dd>

          {/* Bond is a single line: "Not required" when off, or the rate when on.
              Avoids the "Bond required: No" + "Bond %: 1.5%" double-read that
              made it look like bond was being applied. */}
          <dt>Bond</dt>
          <dd>
            {ewo.bond_required
              ? fmtPct(ewo.bond_pct)
              : <span className="rate-unavailable">Not required</span>}
          </dd>

          <dt>Fuel Surcharge %</dt>
          <dd>
            <EditableField
              value={ewo.fuel_surcharge_pct}
              locked={locked}
              type="number"
              step="0.0001"
              min="0"
              placeholder="0.0000"
              onSave={(v) => patchEwo(ewo.id, { fuel_surcharge_pct: v }).then(setEwo)}
            />
          </dd>
        </dl>
      </section>

      <section className="detail-card totals-card">
        <h2 className="detail-card-title">Totals</h2>
        <dl className="detail-grid totals-grid">
          <dt>Labor</dt>        <dd>{fmtMoney(ewo.labor_subtotal)}</dd>
          <dt>Labor OH&P</dt>    <dd>{fmtMoney(ewo.labor_ohp_amount)}</dd>
          <dt>Equip + Mat</dt>   <dd>{fmtMoney(ewo.equip_mat_subtotal)}</dd>
          <dt>Fuel</dt>          <dd>{fmtMoney(ewo.fuel_subtotal)}</dd>
          <dt>E+M OH&P</dt>      <dd>{fmtMoney(ewo.equip_mat_ohp_amount)}</dd>
          <dt>Bond</dt>          <dd>{fmtMoney(ewo.bond_amount)}</dd>
          <dt className="total-row">Total</dt> <dd className="total-row">{fmtMoney(ewo.total)}</dd>
        </dl>
        {ewo.total === null && (
          <p className="hint">
            Add at least one line to a WorkDay to see totals. They recalculate
            automatically as you build; the numbers lock on EWO submission.
          </p>
        )}
      </section>

      <h2 className="section-title">WorkDays ({workDays.length})</h2>
      {workDays.length === 0 ? (
        <div className="empty-state">No WorkDays yet.</div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Foreman</th>
              <th>Location</th>
              <th>Description</th>
              <th>Day Total</th>
            </tr>
          </thead>
          <tbody>
            {workDays.map(wd => (
              <tr key={wd.id}>
                <td>
                  <Link to={`/workdays/${wd.id}`} className="row-link">
                    {wd.work_date}
                  </Link>
                </td>
                <td>{wd.foreman_name || '—'}</td>
                <td>{wd.location || '—'}</td>
                <td className="col-description">{wd.description || <span className="rate-unavailable">—</span>}</td>
                <td>{wd.day_total === null ? <span className="rate-unavailable">—</span> : fmtMoney(wd.day_total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

