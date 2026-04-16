import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  fetchWorkDay, fetchEwo, fetchJob,
  fetchEmployees, fetchEquipment, fetchTrades, fetchMaterialCatalog,
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

  // Reference data for dropdowns + label resolution.
  const [employees, setEmployees] = useState([])
  const [trades, setTrades] = useState([])
  const [equipTypes, setEquipTypes] = useState([])
  const [catalog, setCatalog] = useState([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const employeeMap = useMemo(() => mapById(employees), [employees])
  const tradeMap = useMemo(() => mapById(trades), [trades])
  const equipMap = useMemo(() => mapById(equipTypes), [equipTypes])

  const ewoLocked = ewo && !['open', 'rejected'].includes(ewo.status)

  const reload = useCallback(async () => {
    if (!workDayId) return
    const wd = await fetchWorkDay(workDayId)
    setWorkDay(wd)
    const ewoData = await fetchEwo(wd.ewo)
    setEwo(ewoData)
    const [jobData, la, eq, ma] = await Promise.all([
      fetchJob(ewoData.job),
      laborLines.list({ work_day: wd.id }),
      equipmentLines.list({ work_day: wd.id }),
      materialLines.list({ work_day: wd.id }),
    ])
    setJob(jobData)
    setLabor(la || [])
    setEquipment(eq || [])
    setMaterials(ma || [])
  }, [workDayId])

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        await reload()
        // Reference data in parallel; safe to fire with the core load.
        const [emps, trs, eqs, cat] = await Promise.all([
          fetchEmployees(),
          fetchTrades(),
          fetchEquipment(),
          fetchMaterialCatalog(),
        ])
        if (cancelled) return
        setEmployees(emps || [])
        setTrades(trs || [])
        setEquipTypes(eqs || [])
        setCatalog(cat || [])
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [reload])

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
        <h1 className="page-title">
          WorkDay {workDay.work_date}
          {workDay.foreman_name && (
            <span className="wd-foreman-suffix">· {workDay.foreman_name}</span>
          )}
        </h1>
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

      <LaborSection
        workDayId={workDay.id}
        locked={ewoLocked}
        lines={labor}
        employees={employees}
        trades={trades}
        employeeMap={employeeMap}
        tradeMap={tradeMap}
        onChange={reload}
      />

      <EquipmentSection
        workDayId={workDay.id}
        locked={ewoLocked}
        lines={equipment}
        equipTypes={equipTypes}
        equipMap={equipMap}
        onChange={reload}
      />

      <MaterialSection
        workDayId={workDay.id}
        locked={ewoLocked}
        lines={materials}
        catalog={catalog}
        onChange={reload}
      />
    </div>
  )
}

function mapById(list) {
  const m = new Map()
  list.forEach(x => m.set(x.id, x))
  return m
}

function fmtHours(v) {
  if (v === null || v === undefined || v === '') return '—'
  return Number(v).toFixed(1)
}

function fmtMoney(v) {
  if (v === null || v === undefined || v === '') return <span className="rate-unavailable">—</span>
  return `$${Number(v).toFixed(2)}`
}

// ── Labor ────────────────────────────────────────────────────────────────────

function LaborSection({ workDayId, locked, lines, employees, trades, employeeMap, tradeMap, onChange }) {
  const [adding, setAdding] = useState(false)
  const [err, setErr] = useState(null)

  const [form, setForm] = useState({
    labor_type: 'named',
    employee: '',
    trade_classification: '',
    trade_override_reason: '',
    reg_hours: '8.0',
    ot_hours: '0.0',
    dt_hours: '0.0',
  })

  // When the user picks an employee, default the trade to the employee's.
  const onEmployeeChange = (id) => {
    const emp = employeeMap.get(Number(id))
    setForm(f => ({
      ...f,
      employee: id,
      trade_classification: emp ? String(tradeByName(trades, emp.trade_name)?.id ?? f.trade_classification) : f.trade_classification,
    }))
  }

  const onTypeChange = (type) => {
    setForm(f => ({
      ...f,
      labor_type: type,
      employee: type === 'generic' ? '' : f.employee,
    }))
  }

  const submit = async (e) => {
    e.preventDefault()
    setErr(null)
    const payload = {
      work_day: workDayId,
      labor_type: form.labor_type,
      trade_classification: Number(form.trade_classification),
      reg_hours: form.reg_hours,
      ot_hours: form.ot_hours,
      dt_hours: form.dt_hours,
    }
    if (form.labor_type === 'named') payload.employee = Number(form.employee)
    if (form.trade_override_reason) payload.trade_override_reason = form.trade_override_reason
    try {
      await laborLines.create(payload)
      setAdding(false)
      setForm({
        labor_type: 'named', employee: '', trade_classification: '',
        trade_override_reason: '',
        reg_hours: '8.0', ot_hours: '0.0', dt_hours: '0.0',
      })
      onChange()
    } catch (x) { setErr(x.message) }
  }

  const remove = async (id) => {
    if (!confirm('Delete this labor line?')) return
    try { await laborLines.remove(id); onChange() } catch (x) { alert(x.message) }
  }

  return (
    <>
      <SectionBanner title={`Labor (${lines.length})`}
        onAdd={!locked && !adding ? () => setAdding(true) : null} />
      {adding && (
        <form className="line-form" onSubmit={submit}>
          <LF label="Type">
            <select value={form.labor_type} onChange={e => onTypeChange(e.target.value)}>
              <option value="named">Named</option>
              <option value="generic">Generic</option>
            </select>
          </LF>
          {form.labor_type === 'named' && (
            <LF label="Employee" className="line-form-full">
              <select value={form.employee} onChange={e => onEmployeeChange(e.target.value)} required>
                <option value="">— pick an employee —</option>
                {employees.map(e => (
                  <option key={e.id} value={e.id}>{e.code} · {e.full_name}</option>
                ))}
              </select>
            </LF>
          )}
          <LF label="Trade" className="line-form-full">
            <select value={form.trade_classification}
              onChange={e => setForm({ ...form, trade_classification: e.target.value })}
              required>
              <option value="">— pick a trade —</option>
              {trades.map(t => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
          </LF>
          <LF label="REG hrs">
            <input type="number" inputMode="decimal" step="0.5" min="0" value={form.reg_hours}
              onChange={e => setForm({ ...form, reg_hours: e.target.value })} />
          </LF>
          <LF label="OT hrs">
            <input type="number" inputMode="decimal" step="0.5" min="0" value={form.ot_hours}
              onChange={e => setForm({ ...form, ot_hours: e.target.value })} />
          </LF>
          <LF label="DT hrs">
            <input type="number" inputMode="decimal" step="0.5" min="0" value={form.dt_hours}
              onChange={e => setForm({ ...form, dt_hours: e.target.value })} />
          </LF>
          <LF label="Trade-override reason (only if trade differs from employee default)" className="line-form-full">
            <input type="text" value={form.trade_override_reason}
              onChange={e => setForm({ ...form, trade_override_reason: e.target.value })} />
          </LF>
          {err && <div className="error-state line-form-error">{err}</div>}
          <div className="line-form-actions">
            <button type="button" className="btn" onClick={() => { setAdding(false); setErr(null) }}>Cancel</button>
            <button type="submit" className="btn btn-primary">Add labor line</button>
          </div>
        </form>
      )}
      {lines.length === 0 && !adding ? (
        <div className="empty-state">No labor lines.</div>
      ) : lines.length === 0 ? null : (
        <table className="data-table">
          <thead><tr>
            <th>Type</th><th>Employee</th><th>Trade</th>
            <th>REG</th><th>OT</th><th>DT</th><th>Total</th><th></th>
          </tr></thead>
          <tbody>
            {lines.map(l => (
              <tr key={l.id}>
                <td>{l.labor_type === 'named' ? 'Named' : 'Generic'}</td>
                <td>{l.employee ? employeeMap.get(l.employee)?.full_name || `#${l.employee}` : <span className="rate-unavailable">Generic</span>}</td>
                <td>{tradeMap.get(l.trade_classification)?.name || `#${l.trade_classification}`}</td>
                <td>{fmtHours(l.reg_hours)}</td>
                <td>{fmtHours(l.ot_hours)}</td>
                <td>{fmtHours(l.dt_hours)}</td>
                <td>{fmtMoney(l.line_total)}</td>
                <td>{!locked && <button className="btn-icon" onClick={() => remove(l.id)} title="Delete">×</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  )
}

function tradeByName(trades, name) {
  return trades.find(t => t.name === name)
}

// ── Equipment ────────────────────────────────────────────────────────────────

function EquipmentSection({ workDayId, locked, lines, equipTypes, equipMap, onChange }) {
  const [adding, setAdding] = useState(false)
  const [err, setErr] = useState(null)
  const [categoryFilter, setCategoryFilter] = useState('')
  const [form, setForm] = useState({
    equipment_type: '', qty: '1',
    reg_hours: '8.0', ot_hours: '0.0', standby_hours: '0.0',
  })

  // Distinct category list for the prefilter dropdown.
  const categories = useMemo(() => {
    const set = new Set(equipTypes.map(e => e.category).filter(Boolean))
    return [...set].sort()
  }, [equipTypes])

  // Equipment filtered by the current category selection.
  const filteredEquip = useMemo(() => {
    if (!categoryFilter) return equipTypes
    return equipTypes.filter(e => e.category === categoryFilter)
  }, [equipTypes, categoryFilter])

  // If the user changes the category and the current selection no longer
  // fits, clear it so they don't accidentally submit a stale id.
  const onCategoryChange = (cat) => {
    setCategoryFilter(cat)
    if (form.equipment_type && cat) {
      const current = equipMap.get(Number(form.equipment_type))
      if (current && current.category !== cat) {
        setForm(f => ({ ...f, equipment_type: '' }))
      }
    }
  }

  const submit = async (e) => {
    e.preventDefault()
    setErr(null)
    try {
      await equipmentLines.create({
        work_day: workDayId,
        equipment_type: Number(form.equipment_type),
        qty: Number(form.qty),
        reg_hours: form.reg_hours,
        ot_hours: form.ot_hours,
        standby_hours: form.standby_hours,
      })
      setAdding(false)
      setForm({ equipment_type: '', qty: '1', reg_hours: '8.0', ot_hours: '0.0', standby_hours: '0.0' })
      onChange()
    } catch (x) { setErr(x.message) }
  }

  const remove = async (id) => {
    if (!confirm('Delete this equipment line?')) return
    try { await equipmentLines.remove(id); onChange() } catch (x) { alert(x.message) }
  }

  return (
    <>
      <SectionBanner title={`Equipment (${lines.length})`}
        onAdd={!locked && !adding ? () => setAdding(true) : null} />
      {adding && (
        <form className="line-form" onSubmit={submit}>
          <LF label="Category (narrow the list)" className="line-form-full">
            <select value={categoryFilter} onChange={e => onCategoryChange(e.target.value)}>
              <option value="">— all categories ({equipTypes.length}) —</option>
              {categories.map(c => (
                <option key={c} value={c}>
                  {c} ({equipTypes.filter(e => e.category === c).length})
                </option>
              ))}
            </select>
          </LF>
          <LF label={`Equipment (${filteredEquip.length})`} className="line-form-full">
            <select value={form.equipment_type}
              onChange={e => setForm({ ...form, equipment_type: e.target.value })}
              required>
              <option value="">— pick equipment —</option>
              {filteredEquip.map(e => (
                <option key={e.id} value={e.id}>{e.name} · {e.description}</option>
              ))}
            </select>
          </LF>
          <LF label="Qty">
            <input type="number" inputMode="numeric" min="1" step="1" value={form.qty}
              onChange={e => setForm({ ...form, qty: e.target.value })} />
          </LF>
          <LF label="REG hrs (per unit)">
            <input type="number" inputMode="decimal" step="0.5" min="0" value={form.reg_hours}
              onChange={e => setForm({ ...form, reg_hours: e.target.value })} />
          </LF>
          <LF label="OT hrs (per unit)">
            <input type="number" inputMode="decimal" step="0.5" min="0" value={form.ot_hours}
              onChange={e => setForm({ ...form, ot_hours: e.target.value })} />
          </LF>
          <LF label="Stby hrs (per unit)">
            <input type="number" inputMode="decimal" step="0.5" min="0" value={form.standby_hours}
              onChange={e => setForm({ ...form, standby_hours: e.target.value })} />
          </LF>
          {err && <div className="error-state line-form-error">{err}</div>}
          <div className="line-form-actions">
            <button type="button" className="btn" onClick={() => { setAdding(false); setErr(null) }}>Cancel</button>
            <button type="submit" className="btn btn-primary">Add equipment line</button>
          </div>
        </form>
      )}
      {lines.length === 0 && !adding ? (
        <div className="empty-state">No equipment lines.</div>
      ) : lines.length === 0 ? null : (
        <table className="data-table">
          <thead><tr>
            <th>Equipment</th><th>Qty</th><th>REG</th><th>OT</th><th>Stby</th><th>Total</th><th></th>
          </tr></thead>
          <tbody>
            {lines.map(l => {
              const et = equipMap.get(l.equipment_type)
              return (
                <tr key={l.id}>
                  <td><code>{et?.name || `#${l.equipment_type}`}</code> {et?.description && <span>· {et.description}</span>}</td>
                  <td>{l.qty}</td>
                  <td>{fmtHours(l.reg_hours)}</td>
                  <td>{fmtHours(l.ot_hours)}</td>
                  <td>{fmtHours(l.standby_hours)}</td>
                  <td>{fmtMoney(l.line_total)}</td>
                  <td>{!locked && <button className="btn-icon" onClick={() => remove(l.id)} title="Delete">×</button>}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </>
  )
}

// ── Materials ────────────────────────────────────────────────────────────────

function MaterialSection({ workDayId, locked, lines, catalog, onChange }) {
  const [adding, setAdding] = useState(false)
  const [err, setErr] = useState(null)
  const [form, setForm] = useState({
    catalog_item: '', description: '',
    quantity: '1.000', unit: 'EA', unit_cost: '0.00',
    is_subcontractor: false, reference_number: '',
  })

  const onCatalogChange = (id) => {
    const item = catalog.find(c => String(c.id) === id)
    setForm(f => ({
      ...f,
      catalog_item: id,
      description: item ? item.description : f.description,
      unit: item ? item.default_unit : f.unit,
      unit_cost: item?.last_unit_cost ?? f.unit_cost,
    }))
  }

  const submit = async (e) => {
    e.preventDefault()
    setErr(null)
    try {
      const payload = {
        work_day: workDayId,
        description: form.description,
        quantity: form.quantity,
        unit: form.unit,
        unit_cost: form.unit_cost,
        is_subcontractor: form.is_subcontractor,
      }
      if (form.catalog_item) payload.catalog_item = Number(form.catalog_item)
      if (form.reference_number) payload.reference_number = form.reference_number
      await materialLines.create(payload)
      setAdding(false)
      setForm({ catalog_item: '', description: '', quantity: '1.000', unit: 'EA',
        unit_cost: '0.00', is_subcontractor: false, reference_number: '' })
      onChange()
    } catch (x) { setErr(x.message) }
  }

  const remove = async (id) => {
    if (!confirm('Delete this material line?')) return
    try { await materialLines.remove(id); onChange() } catch (x) { alert(x.message) }
  }

  return (
    <>
      <SectionBanner title={`Materials (${lines.length})`}
        onAdd={!locked && !adding ? () => setAdding(true) : null} />
      {adding && (
        <form className="line-form" onSubmit={submit}>
          <LF label="Catalog item (optional — auto-fills the rest)" className="line-form-full">
            <select value={form.catalog_item} onChange={e => onCatalogChange(e.target.value)}>
              <option value="">— none (type below) —</option>
              {catalog.map(c => (
                <option key={c.id} value={c.id}>
                  {c.description} ({c.default_unit}{c.last_unit_cost ? ` @ $${c.last_unit_cost}` : ''})
                </option>
              ))}
            </select>
          </LF>
          <LF label="Description" className="line-form-full">
            <input type="text" value={form.description}
              onChange={e => setForm({ ...form, description: e.target.value })} required />
          </LF>
          <LF label="Qty">
            <input type="number" inputMode="decimal" step="0.001" min="0" value={form.quantity}
              onChange={e => setForm({ ...form, quantity: e.target.value })} />
          </LF>
          <LF label="Unit">
            <input type="text" value={form.unit}
              onChange={e => setForm({ ...form, unit: e.target.value })} />
          </LF>
          <LF label="$ per unit">
            <input type="number" inputMode="decimal" step="0.01" min="0" value={form.unit_cost}
              onChange={e => setForm({ ...form, unit_cost: e.target.value })} />
          </LF>
          <LF label="Invoice / PO ref" className="line-form-full">
            <input type="text" value={form.reference_number}
              onChange={e => setForm({ ...form, reference_number: e.target.value })} />
          </LF>
          <label className="checkbox-inline line-form-full">
            <input type="checkbox" checked={form.is_subcontractor}
              onChange={e => setForm({ ...form, is_subcontractor: e.target.checked })} />
            Subcontractor
          </label>
          {err && <div className="error-state line-form-error">{err}</div>}
          <div className="line-form-actions">
            <button type="button" className="btn" onClick={() => { setAdding(false); setErr(null) }}>Cancel</button>
            <button type="submit" className="btn btn-primary">Add material line</button>
          </div>
        </form>
      )}
      {lines.length === 0 && !adding ? (
        <div className="empty-state">No material lines.</div>
      ) : lines.length === 0 ? null : (
        <table className="data-table">
          <thead><tr>
            <th>Description</th><th>Qty</th><th>Unit</th><th>$/unit</th><th>Total</th><th>Ref</th><th></th>
          </tr></thead>
          <tbody>
            {lines.map(l => (
              <tr key={l.id}>
                <td>
                  {l.description}
                  {l.is_subcontractor && <span className="badge" style={{ marginLeft: 6 }}>Sub</span>}
                </td>
                <td>{Number(l.quantity).toFixed(3)}</td>
                <td>{l.unit}</td>
                <td>{fmtMoney(l.unit_cost)}</td>
                <td>{fmtMoney(l.line_total)}</td>
                <td>{l.reference_number || <span className="rate-unavailable">—</span>}</td>
                <td>{!locked && <button className="btn-icon" onClick={() => remove(l.id)} title="Delete">×</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  )
}

// ── Shared section banner + labeled form field ─────────────────────────────

function SectionBanner({ title, onAdd }) {
  return (
    <div className="section-banner">
      <h2 className="section-title-inline">{title}</h2>
      {onAdd && <button className="btn btn-primary btn-sm" onClick={onAdd}>+ Add</button>}
    </div>
  )
}

/** LF = labeled field for the inline line-form grid. */
function LF({ label, children, className = '' }) {
  return (
    <label className={`lf ${className}`.trim()}>
      <span className="lf-label">{label}</span>
      {children}
    </label>
  )
}
