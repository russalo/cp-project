import { useEffect, useState } from 'react'

/**
 * Inline-edit cell. Shows the value with a pencil icon when editable;
 * toggling to edit swaps in an <input> (or <textarea> for multiline) with
 * Save / Cancel. Calls `onSave(newValue)` which should return a Promise
 * that resolves with the updated parent record (or just resolves).
 *
 * Props:
 *   value        current value
 *   onSave       async (newValue) => any — called when user saves
 *   locked       when true, shows value as read-only (no pencil)
 *   multiline    render as <textarea>
 *   placeholder  what to show when value is empty/null
 *   type         'text' | 'date' | 'number' (defaults to text)
 *   step, min    forwarded to number inputs
 */
export default function EditableField({
  value,
  onSave,
  locked = false,
  multiline = false,
  placeholder = '—',
  type = 'text',
  step,
  min,
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value ?? '')
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState(null)

  useEffect(() => {
    setDraft(value ?? '')
  }, [value])

  const save = async () => {
    if (String(draft) === String(value ?? '')) {
      setEditing(false)
      return
    }
    setSaving(true)
    setErr(null)
    try {
      await onSave(draft)
      setEditing(false)
    } catch (e) {
      setErr(e.message)
    } finally {
      setSaving(false)
    }
  }

  const cancel = () => {
    setDraft(value ?? '')
    setErr(null)
    setEditing(false)
  }

  if (locked) {
    return <span className="editable-value">{value || <span className="rate-unavailable">{placeholder}</span>}</span>
  }

  if (editing) {
    return (
      <div className={`editable-field editing${multiline ? ' multiline' : ''}`}>
        {multiline ? (
          <textarea
            value={draft}
            autoFocus
            rows={3}
            onChange={e => setDraft(e.target.value)}
          />
        ) : (
          <input
            type={type}
            step={step}
            min={min}
            inputMode={type === 'number' ? 'decimal' : undefined}
            value={draft}
            autoFocus
            onChange={e => setDraft(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') save()
              if (e.key === 'Escape') cancel()
            }}
          />
        )}
        <div className="editable-field-actions">
          <button type="button" className="btn btn-sm" onClick={cancel} disabled={saving}>
            Cancel
          </button>
          <button type="button" className="btn btn-sm btn-primary" onClick={save} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
        {err && <div className="error-state editable-field-error">Error: {err}</div>}
      </div>
    )
  }

  return (
    <div className="editable-field">
      <span className="editable-value">
        {value || <span className="rate-unavailable">{placeholder}</span>}
      </span>
      <button
        type="button"
        className="btn-icon edit-icon"
        onClick={() => setEditing(true)}
        title="Edit"
        aria-label="Edit"
      >
        ✎
      </button>
    </div>
  )
}
