import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { createEwo, fetchJob } from '../services/api'
import { fmtPct } from '../lib/format'

export default function EwoNew() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const [job, setJob] = useState(null)
  const [loadingJob, setLoadingJob] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [form, setForm] = useState({
    ewo_type: 'tm',
    description: '',
    bond_required: false,
    fuel_surcharge_pct: '',
  })

  useEffect(() => {
    let cancelled = false
    fetchJob(jobId)
      .then(d => { if (!cancelled) setJob(d) })
      .catch(err => { if (!cancelled) setError(err.message) })
      .finally(() => { if (!cancelled) setLoadingJob(false) })
    return () => { cancelled = true }
  }, [jobId])

  const submit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      // created_by is inferred server-side (request.user when auth lands;
      // first active user pre-auth). Don't hardcode an ID on the client.
      const body = {
        job: Number(jobId),
        ewo_type: form.ewo_type,
        description: form.description,
        bond_required: form.bond_required,
      }
      if (form.fuel_surcharge_pct !== '') {
        body.fuel_surcharge_pct = form.fuel_surcharge_pct
      }
      const created = await createEwo(body)
      navigate(`/ewos/${created.id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (loadingJob) return <div className="page"><div className="loading-state">Loading…</div></div>
  if (!job) return <div className="page"><div className="error-state">Job not found.</div></div>

  return (
    <div className="page">
      <div className="breadcrumbs">
        <Link to="/jobs">Jobs</Link>
        <span className="breadcrumb-sep">/</span>
        <Link to={`/jobs/${job.id}`}>{job.job_number}</Link>
        <span className="breadcrumb-sep">/</span>
        <span>New EWO</span>
      </div>

      <h1 className="page-title">New EWO — {job.job_number}</h1>
      <p className="hint">
        OH&P and bond percentages snapshot from the job at creation
        (currently Labor {fmtPct(job.labor_ohp_pct)}, E&M {fmtPct(job.equip_mat_ohp_pct)}, Bond {fmtPct(job.bond_pct)}).
        Edit them on the job page first if this EWO needs different rates.
      </p>

      <form onSubmit={submit} className="form-grid">
        <label>
          <span>EWO type</span>
          <select
            value={form.ewo_type}
            onChange={e => setForm({ ...form, ewo_type: e.target.value })}
          >
            <option value="tm">Time & Materials</option>
            <option value="change_order">Change Order / Quote</option>
          </select>
        </label>

        <label>
          <span>Description</span>
          <textarea
            value={form.description}
            onChange={e => setForm({ ...form, description: e.target.value })}
            rows={4}
            required
          />
        </label>

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={form.bond_required}
            onChange={e => setForm({ ...form, bond_required: e.target.checked })}
          />
          <span>Bond required for this EWO</span>
        </label>

        <label>
          <span>Fuel surcharge % (leave blank to seed from last EWO on this job)</span>
          <input
            type="number" step="0.0001" min="0" max="1"
            value={form.fuel_surcharge_pct}
            onChange={e => setForm({ ...form, fuel_surcharge_pct: e.target.value })}
            placeholder="e.g. 0.05 for 5%"
          />
        </label>

        {error && <div className="error-state">Error: {error}</div>}

        <div className="form-actions">
          <Link to={`/jobs/${job.id}`} className="btn">Cancel</Link>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Creating…' : 'Create EWO'}
          </button>
        </div>
      </form>
    </div>
  )
}

