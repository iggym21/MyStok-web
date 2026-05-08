const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function checkOk(res) {
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const getSectors = () =>
  fetch(`${BASE}/sectors`).then(checkOk)

export const recommend = ({ risk_level, duration, sector, top_n = 5 }) =>
  fetch(`${BASE}/recommend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ risk_level, duration, sector, top_n }),
  }).then(checkOk)

export const getStock = (ticker) =>
  fetch(`${BASE}/stocks/${ticker}`).then(checkOk)
