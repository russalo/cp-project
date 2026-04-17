import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchJobs } from '../services/api'

export default function JobList() {
  const [jobs, setJobs] = useState([])
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
        const data = await fetchJobs(showInactive)
        if (!cancelled) setJobs(data)
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [showInactive])

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Jobs</h1>
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
              <th>Job #</th>
              <th>Name</th>
              <th>Location</th>
              <th>GC</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {jobs.length === 0 ? (
              <tr>
                <td colSpan={5} className="rate-unavailable table-empty">
                  No jobs found.
                </td>
              </tr>
            ) : (
              jobs.map(job => (
                <tr key={job.id} className="row-clickable">
                  <td>
                    <Link to={`/jobs/${job.id}`} className="row-link">
                      <code>{job.job_number}</code>
                    </Link>
                  </td>
                  <td><Link to={`/jobs/${job.id}`} className="row-link">{job.name}</Link></td>
                  <td>{job.location || <span className="rate-unavailable">—</span>}</td>
                  <td>{job.gc_name || <span className="rate-unavailable">—</span>}</td>
                  <td>
                    <span className={job.active ? 'badge badge-active' : 'badge badge-inactive'}>
                      {job.active ? 'Active' : 'Inactive'}
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
