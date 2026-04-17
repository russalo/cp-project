import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchJob, fetchEwos } from '../services/api'

const STATUS_LABEL = {
  open: 'Open',
  submitted: 'Submitted',
  approved: 'Approved',
  rejected: 'Rejected',
  sent: 'Sent to GC',
  billed: 'Billed',
}

export default function JobDetail() {
  const { jobId } = useParams()
  const [job, setJob] = useState(null)
  const [ewos, setEwos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [jobData, ewoData] = await Promise.all([
          fetchJob(jobId),
          fetchEwos({ job: jobId }),
        ])
        if (cancelled) return
        setJob(jobData)
        setEwos(ewoData || [])
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [jobId])

  if (loading) return <div className="page"><div className="loading-state">Loading…</div></div>
  if (error) return <div className="page"><div className="error-state">Error: {error}</div></div>
  if (!job) return <div className="page"><div className="error-state">Job not found.</div></div>

  return (
    <div className="page">
      <div className="breadcrumbs">
        <Link to="/jobs">Jobs</Link>
        <span className="breadcrumb-sep">/</span>
        <span>{job.job_number}</span>
      </div>

      <div className="page-header">
        <h1 className="page-title">
          <code>{job.job_number}</code> — {job.name}
        </h1>
        <div className="page-toolbar">
          <Link to={`/jobs/${job.id}/ewos/new`} className="btn btn-primary">+ New EWO</Link>
        </div>
      </div>

      <section className="detail-card">
        <dl className="detail-grid">
          <dt>Location</dt>   <dd>{job.location || '—'}</dd>
          <dt>GC</dt>         <dd>{job.gc_name || '—'}</dd>
          <dt>CP Role</dt>    <dd>{job.cp_role || <span className="rate-unavailable">(unset)</span>}</dd>
          <dt>Labor OH&P</dt> <dd>{fmtPct(job.labor_ohp_pct)}</dd>
          <dt>Equip/Mat OH&P</dt> <dd>{fmtPct(job.equip_mat_ohp_pct)}</dd>
          <dt>Bond</dt>       <dd>{fmtPct(job.bond_pct)}</dd>
          <dt>Status</dt>
          <dd>
            <span className={job.active ? 'badge badge-active' : 'badge badge-inactive'}>
              {job.active ? 'Active' : 'Inactive'}
            </span>
          </dd>
        </dl>
      </section>

      <h2 className="section-title">Extra Work Orders ({ewos.length})</h2>
      {ewos.length === 0 ? (
        <div className="empty-state">No EWOs on this job yet.</div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>EWO #</th>
              <th>Type</th>
              <th>Status</th>
              <th>WorkDays</th>
              <th>Total</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {ewos.map(e => (
              <tr key={e.id}>
                <td><Link to={`/ewos/${e.id}`} className="row-link"><code>{e.ewo_number}</code></Link></td>
                <td>{e.ewo_type === 'tm' ? 'T&M' : 'Change Order'}</td>
                <td>
                  <span className={`badge badge-status-${e.status}`}>
                    {STATUS_LABEL[e.status] || e.status}
                  </span>
                </td>
                <td>{e.workday_count ?? '—'}</td>
                <td>{fmtMoney(e.total)}</td>
                <td className="col-description">{e.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

function fmtPct(v) {
  if (v === null || v === undefined || v === '') return '—'
  return `${(Number(v) * 100).toFixed(2)}%`
}

function fmtMoney(v) {
  if (v === null || v === undefined || v === '') return <span className="rate-unavailable">—</span>
  return `$${Number(v).toFixed(2)}`
}
