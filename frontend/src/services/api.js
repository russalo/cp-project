// API helpers for the CP EWO backend.
//
// All fetches hit relative /api/... paths, routed through Vite's proxy to
// Django's dev server on :8000. Non-2xx responses throw an Error whose
// message is the best available signal (server body first, status fallback).
//
// Nothing here is auth-aware — the backend's permission_classes are AllowAny
// until M4 (DEC-007).

const JSON_HEADERS = { 'Content-Type': 'application/json', Accept: 'application/json' }

async function handle(resOrPromise) {
  // Callers pass handle(fetch(...)) without awaiting, so resOrPromise is a
  // Promise<Response>. Await it here so every caller doesn't have to.
  const res = await resOrPromise
  if (res.status === 204) return null
  const text = await res.text()
  const body = text ? safeJson(text) : null
  if (!res.ok) {
    const msg = formatError(body, res)
    throw new Error(msg)
  }
  return body
}

function safeJson(text) {
  try { return JSON.parse(text) } catch { return text }
}

function formatError(body, res) {
  if (!body) return `${res.status} ${res.statusText}`
  if (typeof body === 'string') return body
  // DRF non-field errors may come back as a plain array of strings.
  if (Array.isArray(body)) return body.join(' | ')
  // DRF returns either { detail: "..." } or { field: [msg, ...] }
  if (body.detail) return body.detail
  const parts = Object.entries(body).map(([k, v]) =>
    `${k}: ${Array.isArray(v) ? v.join('; ') : JSON.stringify(v)}`
  )
  return parts.join(' | ') || `${res.status} ${res.statusText}`
}

function qs(params) {
  const entries = Object.entries(params || {}).filter(([, v]) => v !== undefined && v !== null && v !== '')
  if (!entries.length) return ''
  return '?' + entries.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&')
}

// ─── resources ─────────────────────────────────────────────────────────────

export function fetchEmployees(includeInactive = false) {
  return handle(fetch(`/api/resources/employees/${includeInactive ? '?active=false' : ''}`))
}

export function fetchEquipment(includeInactive = false) {
  return handle(fetch(`/api/resources/equipment/${includeInactive ? '?active=false' : ''}`))
}

export function fetchTrades(includeInactive = false) {
  return handle(fetch(`/api/resources/trades/${includeInactive ? '?active=false' : ''}`))
}

export function fetchMaterialCatalog(includeInactive = false) {
  return handle(fetch(`/api/resources/materials/${includeInactive ? '?active=false' : ''}`))
}

// ─── jobs ──────────────────────────────────────────────────────────────────

export function fetchJobs(includeInactive = false) {
  return handle(fetch(`/api/jobs/${includeInactive ? '?active=false' : ''}`))
}

export function fetchJob(id) {
  return handle(fetch(`/api/jobs/${id}/`))
}

// ─── ewos ──────────────────────────────────────────────────────────────────

export function fetchEwos(params) {
  return handle(fetch(`/api/ewo/ewos/${qs(params)}`))
}

export function fetchEwo(id) {
  return handle(fetch(`/api/ewo/ewos/${id}/`))
}

export function createEwo(data) {
  return handle(fetch('/api/ewo/ewos/', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify(data),
  }))
}

export function patchEwo(id, data) {
  return handle(fetch(`/api/ewo/ewos/${id}/`, {
    method: 'PATCH',
    headers: JSON_HEADERS,
    body: JSON.stringify(data),
  }))
}

// ─── work days ─────────────────────────────────────────────────────────────

export function fetchWorkDays(params) {
  return handle(fetch(`/api/ewo/work-days/${qs(params)}`))
}

export function fetchWorkDay(id) {
  return handle(fetch(`/api/ewo/work-days/${id}/`))
}

export function createWorkDay(data) {
  return handle(fetch('/api/ewo/work-days/', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify(data),
  }))
}

export function patchWorkDay(id, data) {
  return handle(fetch(`/api/ewo/work-days/${id}/`, {
    method: 'PATCH',
    headers: JSON_HEADERS,
    body: JSON.stringify(data),
  }))
}

export function deleteWorkDay(id) {
  return handle(fetch(`/api/ewo/work-days/${id}/`, { method: 'DELETE' }))
}

// ─── line items ────────────────────────────────────────────────────────────

function lineFactory(resource) {
  return {
    list: (params) => handle(fetch(`/api/ewo/${resource}/${qs(params)}`)),
    get: (id) => handle(fetch(`/api/ewo/${resource}/${id}/`)),
    create: (data) => handle(fetch(`/api/ewo/${resource}/`, {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify(data),
    })),
    patch: (id, data) => handle(fetch(`/api/ewo/${resource}/${id}/`, {
      method: 'PATCH',
      headers: JSON_HEADERS,
      body: JSON.stringify(data),
    })),
    remove: (id) => handle(fetch(`/api/ewo/${resource}/${id}/`, { method: 'DELETE' })),
  }
}

export const laborLines = lineFactory('labor-lines')
export const equipmentLines = lineFactory('equipment-lines')
export const materialLines = lineFactory('material-lines')
