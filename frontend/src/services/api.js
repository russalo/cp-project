const BASE = '/api/resources'

export async function fetchEmployees(includeInactive = false) {
  const url = includeInactive ? `${BASE}/employees/?active=false` : `${BASE}/employees/`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export async function fetchEquipment(includeInactive = false) {
  const url = includeInactive ? `${BASE}/equipment/?active=false` : `${BASE}/equipment/`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}
