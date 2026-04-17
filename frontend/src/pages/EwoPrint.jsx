import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  fetchEwo, fetchJob, fetchWorkDays,
  fetchEmployees, fetchEquipment, fetchTrades,
  laborLines, equipmentLines, materialLines,
} from '../services/api'
import { fmtMoney, fmtHours, fmtPct } from '../lib/format'
import headerLockup from '../assets/header.svg'

const STATUS_LABEL = {
  open: 'Open',
  submitted: 'Submitted',
  approved: 'Approved',
  rejected: 'Rejected',
  sent: 'Sent to GC',
  billed: 'Billed',
}

/**
 * Printable claim package for an EWO.
 *
 *   Page 1:  Letterhead + summary + rolled-up totals + WorkDay index
 *   Page N:  One detail sheet per WorkDay (labor / equipment / materials
 *            + daily totals + signature block)
 *
 * Print CSS lives inside this component via a <style> block so the rules
 * don't leak to other pages. Browser's built-in print → PDF is the
 * output path; we don't generate PDFs server-side yet.
 */
export default function EwoPrint() {
  const { ewoId } = useParams()
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const ewo = await fetchEwo(ewoId)
        const [job, wds, emps, trs, eqs] = await Promise.all([
          fetchJob(ewo.job),
          fetchWorkDays({ ewo: ewo.id }),
          fetchEmployees(),
          fetchTrades(),
          fetchEquipment(),
        ])
        // For each WorkDay, pull its line items in parallel.
        const perDay = await Promise.all((wds || []).map(async (wd) => {
          const [labor, equipment, materials] = await Promise.all([
            laborLines.list({ work_day: wd.id }),
            equipmentLines.list({ work_day: wd.id }),
            materialLines.list({ work_day: wd.id }),
          ])
          return { wd, labor: labor || [], equipment: equipment || [], materials: materials || [] }
        }))
        if (!cancelled) setData({ ewo, job, days: perDay, employees: emps, trades: trs, equipment: eqs })
      } catch (e) {
        if (!cancelled) setErr(e.message)
      }
    }
    load()
    return () => { cancelled = true }
  }, [ewoId])

  const empMap = useMemo(() => mapById(data?.employees), [data])
  const tradeMap = useMemo(() => mapById(data?.trades), [data])
  const eqMap = useMemo(() => mapById(data?.equipment), [data])

  if (err) return <div className="page"><div className="error-state">Error: {err}</div></div>
  if (!data) return <div className="page"><div className="loading-state">Loading…</div></div>

  const { ewo, job, days } = data

  return (
    <>
      <PrintStyles />

      {/* Toolbar (non-printing) */}
      <div className="print-toolbar no-print">
        <Link to={`/ewos/${ewo.id}`} className="btn">← Back</Link>
        <button className="btn btn-primary" onClick={() => window.print()}>Print / Save as PDF</button>
      </div>

      {/* License footer — fixed to the bottom of every printed page via
          @media print rules below. Hidden on screen except when printing. */}
      <div className="print-footer">
        State Contractors Lic. No. 304795-Class "A"
      </div>

      {/* ── Page 1: Cover + summary ─────────────────────────────────────── */}
      <article className="printable print-page">
        <Letterhead />

        <h1 className="print-doc-title">
          Daily Time &amp; Material Report
          <code className="print-doc-ewo">{ewo.ewo_number}</code>
          <span className="print-day-pill">{STATUS_LABEL[ewo.status] || ewo.status}</span>
        </h1>

        {/* Dense 3-column metadata strip. Labels above values so "Job",
            "Job Site", "GC" line up in a scannable row. */}
        <section className="print-meta-strip">
          <div>
            <div className="print-meta-label">Job</div>
            <div className="print-meta-value"><code>{job.job_number}</code> {job.name}</div>
          </div>
          <div>
            <div className="print-meta-label">Job Site</div>
            <div className="print-meta-value">{job.location || '—'}</div>
          </div>
          <div>
            <div className="print-meta-label">General Contractor</div>
            <div className="print-meta-value">{job.gc_name || '—'}</div>
          </div>
          <div>
            <div className="print-meta-label">Type</div>
            <div className="print-meta-value">
              {ewo.ewo_type === 'tm' ? 'Time & Materials' : 'Change Order'}
            </div>
          </div>
          <div>
            <div className="print-meta-label">OH&amp;P</div>
            <div className="print-meta-value">{ohpLine(ewo)}</div>
          </div>
          <div>
            <div className="print-meta-label">Bond</div>
            <div className="print-meta-value">
              {ewo.bond_required ? fmtPct(ewo.bond_pct) : 'Not required'}
            </div>
          </div>
          <div>
            <div className="print-meta-label">Fuel Surcharge</div>
            <div className="print-meta-value">
              {Number(ewo.fuel_surcharge_pct) > 0 ? fmtPct(ewo.fuel_surcharge_pct) : 'None'}
            </div>
          </div>
          {(ewo.gc_ack_name || ewo.gc_ack_date) && (
            <div>
              <div className="print-meta-label">GC Acknowledgement</div>
              <div className="print-meta-value">
                {ewo.gc_ack_name || '—'}
                {ewo.gc_ack_date && ` · ${ewo.gc_ack_date}`}
                {ewo.gc_ack_method && ` · ${ewo.gc_ack_method}`}
              </div>
            </div>
          )}
        </section>

        <section className="print-description">
          <div className="print-meta-label">Description</div>
          <div className="print-meta-value">{ewo.description || '—'}</div>
        </section>

        <h2 className="print-section-title">WorkDay Summary ({days.length})</h2>
        <table className="print-daylist">
          <thead>
            <tr>
              <th>Date</th>
              <th>Foreman</th>
              <th>Location</th>
              <th>Description</th>
              <th className="num">Day Total</th>
            </tr>
          </thead>
          <tbody>
            {days.map(({ wd }) => (
              <tr key={wd.id}>
                <td>{wd.work_date}</td>
                <td>{wd.foreman_name || '—'}</td>
                <td>{wd.location || '—'}</td>
                <td>{wd.description || ''}</td>
                <td className="num">{fmtMoney(wd.day_total)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <h2 className="print-section-title">EWO Totals</h2>
        <table className="print-totals">
          <tbody>
            <tr><td>Labor</td><td>{fmtMoney(ewo.labor_subtotal)}</td></tr>
            <tr><td>Equipment + Materials</td><td>{fmtMoney(ewo.equip_mat_subtotal)}</td></tr>
            <tr><td>Fuel</td><td>{fmtMoney(ewo.fuel_subtotal)}</td></tr>
            <tr><td>OH&amp;P ({fmtPct(ewo.labor_ohp_pct)})</td><td>{fmtMoney(sumOhp(ewo))}</td></tr>
            <tr><td>Bond</td><td>{fmtMoney(ewo.bond_amount)}</td></tr>
            <tr className="print-total-row">
              <td>TOTAL</td>
              <td>{fmtMoney(ewo.total)}</td>
            </tr>
          </tbody>
        </table>

        <p className="print-footer-note">
          Continues on following pages — one sheet per WorkDay.
        </p>
      </article>

      {/* ── Page N: one WorkDay per page ───────────────────────────────── */}
      {days.map(({ wd, labor, equipment, materials }) => (
        <article className="printable print-page print-page-break" key={wd.id}>
          <Letterhead />

          <h1 className="print-doc-title">
            Daily T&amp;M Sheet — <code>{ewo.ewo_number}</code>
            <span className="print-day-pill">{wd.work_date}</span>
          </h1>

          <section className="print-meta-strip">
            <div>
              <div className="print-meta-label">Job</div>
              <div className="print-meta-value"><code>{job.job_number}</code> {job.name}</div>
            </div>
            <div>
              <div className="print-meta-label">Foreman</div>
              <div className="print-meta-value">{wd.foreman_name || '—'}</div>
            </div>
            <div>
              <div className="print-meta-label">Superintendent</div>
              <div className="print-meta-value">{wd.superintendent_name || '—'}</div>
            </div>
            <div>
              <div className="print-meta-label">Location</div>
              <div className="print-meta-value">{wd.location || '—'}</div>
            </div>
            <div>
              <div className="print-meta-label">Weather</div>
              <div className="print-meta-value">{wd.weather || '—'}</div>
            </div>
          </section>

          {wd.description && (
            <section className="print-description">
              <div className="print-meta-label">Description</div>
              <div className="print-meta-value">{wd.description}</div>
            </section>
          )}

          <h2 className="print-section-title">Labor</h2>
          {labor.length === 0 ? (
            <p className="print-empty">No labor lines.</p>
          ) : (
            <table className="print-lines">
              <colgroup>
                <col /><col />
                <col className="col-hrs" />
                <col className="col-hrs" />
                <col className="col-hrs" />
                <col className="col-money" />
                <col className="col-total" />
              </colgroup>
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Trade</th>
                  <th className="num">REG</th>
                  <th className="num">OT</th>
                  <th className="num">DT</th>
                  <th className="num">Rate</th>
                  <th className="num">Total</th>
                </tr>
              </thead>
              <tbody>
                {labor.map(l => (
                  <tr key={l.id}>
                    <td>{l.employee ? empMap.get(l.employee)?.full_name || `#${l.employee}` : <em>Generic</em>}</td>
                    <td>{tradeMap.get(l.trade_classification)?.name || `#${l.trade_classification}`}</td>
                    <td className="num">{fmtHours(l.reg_hours)}</td>
                    <td className="num">{fmtHours(l.ot_hours)}</td>
                    <td className="num">{fmtHours(l.dt_hours)}</td>
                    <td className="num">{l.rate_reg_snapshot ? fmtMoney(l.rate_reg_snapshot) : '—'}</td>
                    <td className="num">{fmtMoney(l.line_total)}</td>
                  </tr>
                ))}
                <tr className="print-subtotal-row">
                  <td colSpan={6}>Labor Subtotal</td>
                  <td className="num">{fmtMoney(wd.labor_subtotal)}</td>
                </tr>
              </tbody>
            </table>
          )}

          <h2 className="print-section-title">Equipment</h2>
          {equipment.length === 0 ? (
            <p className="print-empty">No equipment lines.</p>
          ) : (
            <table className="print-lines">
              <colgroup>
                <col className="col-code" />
                <col />
                <col className="col-hrs" />
                <col className="col-hrs" />
                <col className="col-hrs" />
                <col className="col-hrs" />
                <col className="col-total" />
              </colgroup>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Description</th>
                  <th className="num">Qty</th>
                  <th className="num">REG</th>
                  <th className="num">OT</th>
                  <th className="num">Stby</th>
                  <th className="num">Total</th>
                </tr>
              </thead>
              <tbody>
                {equipment.map(e => {
                  const et = eqMap.get(e.equipment_type)
                  return (
                    <tr key={e.id}>
                      <td><code>{et?.name || `#${e.equipment_type}`}</code></td>
                      <td>{et?.description || '—'}</td>
                      <td className="num">{e.qty}</td>
                      <td className="num">{fmtHours(e.reg_hours)}</td>
                      <td className="num">{fmtHours(e.ot_hours)}</td>
                      <td className="num">{fmtHours(e.standby_hours)}</td>
                      <td className="num">{fmtMoney(e.line_total)}</td>
                    </tr>
                  )
                })}
                <tr className="print-subtotal-row">
                  <td colSpan={6}>Equipment Subtotal</td>
                  <td className="num">{fmtMoney(wd.equip_subtotal)}</td>
                </tr>
              </tbody>
            </table>
          )}

          <h2 className="print-section-title">Materials</h2>
          {materials.length === 0 ? (
            <p className="print-empty">No material lines.</p>
          ) : (
            <table className="print-lines">
              <colgroup>
                <col />
                <col className="col-qty-dec" />
                <col className="col-unit" />
                <col className="col-money" />
                <col className="col-total" />
              </colgroup>
              <thead>
                <tr>
                  <th>Description</th>
                  <th className="num">Qty</th>
                  <th>Unit</th>
                  <th className="num">Unit Cost</th>
                  <th className="num">Total</th>
                </tr>
              </thead>
              <tbody>
                {materials.map(m => (
                  <tr key={m.id}>
                    <td>{m.description}{m.is_subcontractor ? ' (sub)' : ''}</td>
                    <td className="num">{Number(m.quantity).toFixed(2)}</td>
                    <td>{m.unit}</td>
                    <td className="num">{fmtMoney(m.unit_cost)}</td>
                    <td className="num">{fmtMoney(m.line_total)}</td>
                  </tr>
                ))}
                <tr className="print-subtotal-row">
                  <td colSpan={4}>Materials Subtotal</td>
                  <td className="num">{fmtMoney(wd.material_subtotal)}</td>
                </tr>
              </tbody>
            </table>
          )}

          <section className="print-day-summary">
            <table className="print-kv">
              <tbody>
                <tr><td>Labor OH&amp;P ({fmtPct(ewo.labor_ohp_pct)})</td><td>{fmtMoney(wd.labor_ohp_amount)}</td></tr>
                <tr><td>Fuel surcharge</td><td>{fmtMoney(wd.fuel_amount)}</td></tr>
                <tr><td>Equip/Mat OH&amp;P ({fmtPct(ewo.equip_mat_ohp_pct)})</td><td>{fmtMoney(wd.equip_mat_ohp_amount)}</td></tr>
                {ewo.bond_required && (
                  <tr><td>Bond ({fmtPct(ewo.bond_pct)})</td><td>{fmtMoney(wd.bond_amount)}</td></tr>
                )}
                <tr className="print-total-row">
                  <td>DAY TOTAL</td>
                  <td>{fmtMoney(wd.day_total)}</td>
                </tr>
              </tbody>
            </table>
          </section>

          <section className="print-signatures">
            <div className="print-sig-line">
              <div className="print-sig-slot"></div>
              <div className="print-sig-label">FOREMAN — signature &amp; date</div>
            </div>
            <div className="print-sig-line">
              <div className="print-sig-slot"></div>
              <div className="print-sig-label">INSPECTOR — signature, org &amp; date</div>
            </div>
          </section>
        </article>
      ))}
    </>
  )
}

function Letterhead() {
  // header.svg already includes mark + wordmark + tagline + Est. 1966 +
  // phone/fax/addresses as one pre-rendered lockup. No separate contact
  // block needed on the right.
  return (
    <header className="print-letterhead">
      <img
        src={headerLockup}
        alt="C.P. Construction Company, Inc."
        className="print-letterhead-lockup"
      />
    </header>
  )
}

function mapById(list) {
  const m = new Map()
  if (!list) return m
  list.forEach(x => m.set(x.id, x))
  return m
}

function ohpLine(ewo) {
  const l = Number(ewo.labor_ohp_pct ?? 0)
  const em = Number(ewo.equip_mat_ohp_pct ?? 0)
  if (l === em) return fmtPct(l)
  return `L ${fmtPct(l)} · EM ${fmtPct(em)}`
}

function sumOhp(ewo) {
  const l = Number(ewo.labor_ohp_amount ?? 0)
  const em = Number(ewo.equip_mat_ohp_amount ?? 0)
  if (ewo.labor_ohp_amount === null && ewo.equip_mat_ohp_amount === null) return null
  return l + em
}

/* Print styles are scoped within a <style> block so they don't bleed into
 * the rest of the app. On-screen, .printable renders with a light page
 * background and shadow so it looks paper-like before printing. */
function PrintStyles() {
  return (
    <style>{`
      .no-print { display: flex; gap: 8px; padding: 12px 16px;
                  background: var(--cp-gray-lt); border-bottom: 1px solid var(--border); }

      .printable {
        background: #fff;
        color: #000;
        font-family: 'Square721 BT', 'Roboto', system-ui, sans-serif;
        font-size: 10pt;
        line-height: 1.3;
        padding: 0.5in 0.5in;
        max-width: 8.5in;
        margin: 16px auto;
        box-shadow: 0 2px 12px rgba(0,0,0,0.15);
      }
      .print-page-break { page-break-before: always; break-before: page; }

      .print-letterhead {
        border-bottom: 2px solid #2e2e2e;
        padding-bottom: 8pt;
        margin-bottom: 14pt;
      }
      .print-letterhead-lockup {
        /* Full lockup SVG (mark + wordmark + tagline + Est. + contact).
           Sized to the full content width so the contact block on the
           right sits at the page's right margin. */
        width: 100%;
        height: auto;
        display: block;
      }

      .print-doc-title {
        font-family: 'Square721 BT Extended', 'Arial Black', sans-serif;
        font-size: 13pt;
        margin: 0 0 10px;
        color: #2e2e2e;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        display: flex;
        align-items: baseline;
        gap: 12px;
      }
      .print-doc-title code { font-size: 13pt; background: none; padding: 0; color: #f37224; }
      .print-day-pill {
        font-size: 10pt; color: #333; letter-spacing: 0;
        border: 1px solid #ccc; padding: 2px 8px; border-radius: 3px;
        text-transform: none;
        margin-left: auto;
      }

      /* Legacy stacked meta block, still used on per-WorkDay detail sheets
         where the vertical layout makes sense. */
      .print-meta dl {
        display: grid;
        grid-template-columns: 120px 1fr;
        gap: 2pt 10pt;
        margin: 6pt 0 8pt;
      }
      .print-meta dt {
        font-weight: 700;
        text-transform: uppercase;
        font-size: 7pt;
        letter-spacing: 0.6px;
        color: #555;
      }
      .print-meta dd { margin: 0; color: #000; font-size: 9.5pt; }

      /* Dense 3-column strip for the summary page — label above value in
         each cell, ~7 fields fit across two rows. */
      .print-meta-strip {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8pt 14pt;
        margin: 8pt 0 6pt;
        padding: 6pt 0;
        border-top: 0.5pt solid #ccc;
        border-bottom: 0.5pt solid #ccc;
      }
      .print-meta-strip > div { min-width: 0; }
      .print-meta-label {
        font-family: 'Square721 BT', 'Roboto', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 7pt;
        letter-spacing: 0.8px;
        color: #666;
        margin-bottom: 1pt;
      }
      .print-meta-value {
        font-size: 10pt;
        color: #000;
        line-height: 1.25;
        word-wrap: break-word;
      }
      .print-meta-value code {
        font-size: 9.5pt;
        padding: 1pt 4pt;
        background: #f0f0ee;
        border-radius: 2pt;
      }

      .print-description {
        margin: 4pt 0 8pt;
      }
      .print-description .print-meta-value {
        font-size: 10.5pt;
        line-height: 1.35;
        padding: 3pt 0;
      }

      .print-doc-ewo {
        font-size: 14pt !important;
        background: none !important;
        padding: 0 !important;
        color: #f37224 !important;
      }

      .print-section-title {
        font-family: 'Square721 BT Extended', 'Arial Black', sans-serif;
        font-size: 9pt;
        background: #2e2e2e;
        color: #fff;
        padding: 3pt 9pt;
        margin: 9pt 0 0;
        text-transform: uppercase;
        letter-spacing: 1px;
      }

      .print-lines, .print-totals, .print-kv, .print-daylist {
        width: 100%; border-collapse: collapse; font-size: 9pt;
      }
      /* Fixed layout so the colgroup widths below actually pin the columns.
         Without this the browser auto-fits and REG/OT/DT/Total drift
         between Labor, Equipment, and Materials tables. */
      .print-lines { table-layout: fixed; }
      .print-lines td, .print-lines th {
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
      }
      .print-lines td:first-child, .print-lines th:first-child,
      .print-lines td:nth-child(2), .print-lines th:nth-child(2) {
        white-space: normal;
      }
      .col-hrs     { width: 40pt; }
      .col-qty-dec { width: 44pt; }
      .col-unit    { width: 40pt; }
      .col-money   { width: 72pt; }
      .col-total   { width: 76pt; }
      .col-code    { width: 72pt; }
      .print-lines thead th {
        background: #e5e5e4; color: #000;
        text-align: left; padding: 3pt 7pt; font-weight: 700;
        text-transform: uppercase; font-size: 7.5pt; letter-spacing: 0.5px;
        border-bottom: 1px solid #999;
      }
      /* Numeric headers must right-align to match the values underneath;
         .num alone loses the specificity battle against the rule above. */
      .print-lines thead th.num { text-align: right; }
      .print-lines tbody td, .print-daylist tbody td {
        padding: 3pt 7pt; border-bottom: 0.5pt solid #bbb;
      }
      .print-daylist thead th {
        background: #e5e5e4; padding: 3pt 7pt; font-weight: 700;
        text-transform: uppercase; font-size: 7.5pt; letter-spacing: 0.5px;
        text-align: left;
      }

      .num { text-align: right; font-variant-numeric: tabular-nums; }
      .print-lines .print-subtotal-row td {
        border-top: 1px solid #000; border-bottom: none;
        font-weight: 700; background: #f8f8f7; padding-top: 6px;
      }

      .print-markups { margin: 4px 0 0; }
      .print-kv td { padding: 3px 6px; }
      .print-kv td:first-child { color: #555; text-transform: uppercase;
        font-size: 8pt; letter-spacing: 0.5px; white-space: nowrap; }
      .print-kv td:last-child { text-align: right; font-family: var(--mono); }

      .print-totals {
        margin-top: 6px;
        border: 1px solid #ccc;
      }
      .print-totals td { padding: 5px 10px; border-bottom: 0.5pt solid #ddd; }
      .print-totals td:first-child { color: #333; text-transform: uppercase;
        font-size: 9pt; letter-spacing: 0.5px; }
      .print-totals td:last-child { text-align: right; font-variant-numeric: tabular-nums; }
      .print-totals .print-total-row td {
        font-weight: 900; font-size: 12pt; color: #0d0d0d;
        border-top: 2px solid #2e2e2e; border-bottom: none;
        background: #e5e5e4;
      }

      .print-day-summary { margin-top: 6pt; width: auto; margin-left: auto; }
      .print-day-summary .print-kv { width: auto; min-width: 50%; margin-left: auto; }
      .print-day-summary .print-total-row td {
        font-weight: 900; font-size: 10pt;
        border-top: 1.5px solid #2e2e2e; background: #f37224; color: #fff;
      }

      .print-signatures {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14pt;
        margin-top: 18pt;
        page-break-inside: avoid;
        break-inside: avoid;
      }
      .print-sig-line {
        /* container only — actual line is the slot's bottom border. */
      }
      .print-sig-slot {
        height: 36pt;                    /* writing space */
        border-bottom: 1px solid #000;   /* THIS is the signature line */
      }
      .print-sig-label {
        margin-top: 2pt;                 /* label sits right under the line */
        font-size: 7.5pt;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #555;
      }

      /* Try to keep each day's sheet on a single page. The break-before
         rule above forces a new page at the start; combined with
         break-inside here the browser will keep the content together
         when the content fits. */
      .print-page-break {
        break-inside: avoid-page;
      }

      .print-empty {
        margin: 6px 0 10px; font-size: 9pt; color: #777; font-style: italic;
        padding: 4px 10px; border-left: 2px solid #ccc;
      }

      .print-footer-note {
        margin-top: 24px; font-size: 8pt; color: #888;
        text-align: right; font-style: italic;
      }

      /* Screen-side: hide the license footer (it belongs at the bottom of
         printed pages, not in the on-screen flow). */
      .print-footer { display: none; }

      @media print {
        /* Hide the shared app chrome so the printed pages are just the
           report content — no black header bar, no JOBS/EMPLOYEES/
           EQUIPMENT tab strip, no print-toolbar. */
        .app-header,
        .tab-strip,
        .no-print {
          display: none !important;
        }
        body { background: #fff !important; }

        /* @page margin is the SINGLE gutter. Dropping .printable padding
           prevents the double-margin that was pushing the letterhead's
           right-side contact block off the page. */
        @page { size: Letter; margin: 0.5in 0.5in 0.7in 0.5in; }
        .printable {
          box-shadow: none;
          margin: 0;
          padding: 0;
          max-width: none;
        }

        /* Never let the full-bleed letterhead kiss the right edge. */
        .print-letterhead-lockup {
          max-width: 100%;
          width: 100%;
        }

        /* License footer — pinned to the bottom of every printed page.
           Chrome / Safari respect position:fixed per-page when printing. */
        .print-footer {
          display: block;
          position: fixed;
          bottom: 0;
          left: 0;
          right: 0;
          text-align: center;
          font-family: 'Square721 BT', 'Roboto', sans-serif;
          font-size: 8pt;
          font-weight: 700;
          color: #f37224;
          padding: 6pt 0;
          letter-spacing: 0.4pt;
        }
      }
    `}</style>
  )
}
