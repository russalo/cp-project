import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  fetchWorkDay, fetchEwo, fetchJob,
  laborLines, equipmentLines, materialLines,
} from '../services/api'

export default function WorkDayDetail() {
  const { workDayId } = useParams()
  const [workDay, setWorkDay] = useState(null)
  const [ewo, setEwo] = useState(null)
  const [job, setJob] = useState(null)
  const [labor, setLabor] = useState([])
  const [equipment, setEquipment] = useState([])
  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const wd = await fetchWorkDay(workDayId)
        if (cancelled) return
        setWorkDay(wd)
        const ewoData = await fetchEwo(wd.ewo)
        if (cancelled) return
        setEwo(ewoData)
        const [jobData, la, eq, ma] = await Promise.all([
          fetchJob(ewoData.job),
          laborLines.list({ work_day: wd.id }),
          equipmentLines.list({ work_day: wd.id }),
          materialLines.list({ work_day: wd.id }),
        ])
        if (cancelled) return
        setJob(jobData)
        setLabor(la || [])
        setEquipment(eq || [])
        setMaterials(ma || [])
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [workDayId])

  if (loading) return <div className="page"><div className="loading-state">Loading…</div></div>
  if (error) return <div className="page"><div className="error-state">Error: {error}</div></div>
  if (!workDay) return <div className="page"><div className="error-state">WorkDay not found.</div></div>

  return (
    <div className="page">
      <div className="breadcrumbs">
        <Link to="/jobs">Jobs</Link>
        <span className="breadcrumb-sep">/</span>
        {job ? <Link to={`/jobs/${job.id}`}>{job.job_number}</Link> : '…'}
        <span className="breadcrumb-sep">/</span>
        {ewo ? <Link to={`/ewos/${ewo.id}`}>{ewo.ewo_number}</Link> : '…'}
        <span className="breadcrumb-sep">/</span>
        <span>{workDay.work_date}</span>
      </div>

      <div className="page-header">
        <h1 className="page-title">WorkDay {workDay.work_date}</h1>
      </div>

      <section className="detail-card">
        <dl className="detail-grid">
          <dt>Foreman</dt>        <dd>{workDay.foreman_name || '—'}</dd>
          <dt>Superintendent</dt> <dd>{workDay.superintendent_name || '—'}</dd>
          <dt>Location</dt>       <dd>{workDay.location || '—'}</dd>
          <dt>Weather</dt>        <dd>{workDay.weather || '—'}</dd>
          <dt>Day Total</dt>      <dd>{fmtMoney(workDay.day_total)}</dd>
        </dl>
        {workDay.description && (
          <p className="description-block">{workDay.description}</p>
        )}
      </section>

      <LineSection
        title={`Labor (${labor.length})`}
        headers={['Type', 'Employee', 'Trade', 'REG', 'OT', 'DT', 'Line Total']}
        rows={labor.map(l => [
          l.labor_type === 'named' ? 'Named' : 'Generic',
          employeeLabel(l),
          tradeLabel(l),
          fmtHours(l.reg_hours),
          fmtHours(l.ot_hours),
          fmtHours(l.dt_hours),
          fmtMoney(l.line_total),
        ])}
      />

      <LineSection
        title={`Equipment (${equipment.length})`}
        headers={['Equipment', 'Qty', 'REG', 'OT', 'Standby', 'Line Total']}
        rows={equipment.map(e => [
          <EquipmentLabel line={e} key="eq" />,
          e.qty,
          fmtHours(e.reg_hours),
          fmtHours(e.ot_hours),
          fmtHours(e.standby_hours),
          fmtMoney(e.line_total),
        ])}
      />

      <LineSection
        title={`Materials (${materials.length})`}
        headers={['Description', 'Qty', 'Unit', 'Unit Cost', 'Line Total', 'Sub/Ref']}
        rows={materials.map(m => [
          m.description,
          m.quantity,
          m.unit,
          fmtMoney(m.unit_cost),
          fmtMoney(m.line_total),
          [m.is_subcontractor ? 'Sub' : '', m.reference_number].filter(Boolean).join(' · ') || '—',
        ])}
      />
    </div>
  )
}

function LineSection({ title, headers, rows }) {
  return (
    <>
      <h2 className="section-title">{title}</h2>
      {rows.length === 0 ? (
        <div className="empty-state">None.</div>
      ) : (
        <table className="data-table">
          <thead><tr>{headers.map(h => <th key={h}>{h}</th>)}</tr></thead>
          <tbody>
            {rows.map((cells, i) => (
              <tr key={i}>
                {cells.map((c, j) => <td key={j}>{c}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  )
}

function employeeLabel(l) {
  // Only id is returned; the serializer embeds trade_classification as pk too.
  // Richer labels require a resolver; shown as "ID ###" for now.
  return l.employee ? `#${l.employee}` : <span className="rate-unavailable">Generic</span>
}

function tradeLabel(l) {
  return l.trade_classification ? `#${l.trade_classification}` : '—'
}

function EquipmentLabel({ line }) {
  return <span>#{line.equipment_type}</span>
}

function fmtHours(v) {
  if (v === null || v === undefined || v === '') return '—'
  return Number(v).toFixed(1)
}

function fmtMoney(v) {
  if (v === null || v === undefined || v === '') return <span className="rate-unavailable">—</span>
  return `$${Number(v).toFixed(2)}`
}
