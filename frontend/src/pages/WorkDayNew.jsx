import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { createWorkDay, fetchEwo, fetchJob } from '../services/api'

export default function WorkDayNew() {
  const { ewoId } = useParams()
  const navigate = useNavigate()
  const [ewo, setEwo] = useState(null)
  const [job, setJob] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [form, setForm] = useState({
    // Use a locale-aware date so users in timezones behind UTC don't get
    // tomorrow's date after sunset. 'sv-SE' happens to format as YYYY-MM-DD.
    work_date: new Date().toLocaleDateString('sv-SE'),
    foreman_name: '',
    superintendent_name: '',
    weather: '',
    location: '',
    description: '',
  })

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const ewoData = await fetchEwo(ewoId)
        if (cancelled) return
        setEwo(ewoData)
        const jobData = await fetchJob(ewoData.job)
        if (cancelled) return
        setJob(jobData)
        // Default WorkDay location from Job.location if not overridden.
        setForm(f => ({ ...f, location: jobData.location || '' }))
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [ewoId])

  const submit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const created = await createWorkDay({
        ewo: Number(ewoId),
        ...form,
      })
      navigate(`/workdays/${created.id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="page"><div className="loading-state">Loading…</div></div>
  if (!ewo) return <div className="page"><div className="error-state">EWO not found.</div></div>

  return (
    <div className="page">
      <div className="breadcrumbs">
        <Link to="/jobs">Jobs</Link>
        <span className="breadcrumb-sep">/</span>
        {job ? <Link to={`/jobs/${job.id}`}>{job.job_number}</Link> : '…'}
        <span className="breadcrumb-sep">/</span>
        <Link to={`/ewos/${ewo.id}`}>{ewo.ewo_number}</Link>
        <span className="breadcrumb-sep">/</span>
        <span>New WorkDay</span>
      </div>

      <h1 className="page-title">New WorkDay — {ewo.ewo_number}</h1>

      <form onSubmit={submit} className="form-grid">
        <label>
          <span>Work date</span>
          <input
            type="date"
            value={form.work_date}
            onChange={e => setForm({ ...form, work_date: e.target.value })}
            required
          />
        </label>

        <label>
          <span>Foreman</span>
          <input
            type="text"
            value={form.foreman_name}
            onChange={e => setForm({ ...form, foreman_name: e.target.value })}
            placeholder="e.g. Larry Gregory"
          />
        </label>

        <label>
          <span>Superintendent</span>
          <input
            type="text"
            value={form.superintendent_name}
            onChange={e => setForm({ ...form, superintendent_name: e.target.value })}
          />
        </label>

        <label>
          <span>Location</span>
          <input
            type="text"
            value={form.location}
            onChange={e => setForm({ ...form, location: e.target.value })}
          />
        </label>

        <label>
          <span>Weather</span>
          <input
            type="text"
            value={form.weather}
            onChange={e => setForm({ ...form, weather: e.target.value })}
            placeholder="e.g. Clear, 78°F"
          />
        </label>

        <label>
          <span>Description</span>
          <textarea
            value={form.description}
            onChange={e => setForm({ ...form, description: e.target.value })}
            rows={3}
            placeholder="What happened this day?"
          />
        </label>

        {error && <div className="error-state">Error: {error}</div>}

        <div className="form-actions">
          <Link to={`/ewos/${ewo.id}`} className="btn">Cancel</Link>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Creating…' : 'Create WorkDay'}
          </button>
        </div>
      </form>
    </div>
  )
}
