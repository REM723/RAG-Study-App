const BASE = 'http://localhost:8000'

async function req(path, opts = {}) {
  const res = await fetch(BASE + path, opts)
  if (!res.ok) {
    let detail = res.statusText
    try { detail = (await res.json()).detail || detail } catch { /* non-JSON */ }
    throw new Error(detail)
  }
  return res.status === 204 ? null : res.json()
}

const json = (body) => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const api = {
  documents: () => req('/documents'),
  upload: (files) => {
    const fd = new FormData()
    for (const f of files) fd.append('files', f)
    return req('/documents/upload', { method: 'POST', body: fd })
  },
  ingest: () => req('/documents/ingest', { method: 'POST' }),
  deleteDoc: (id) => req(`/documents/${id}`, { method: 'DELETE' }),
  genMcq: (count) => req('/questions/mcq', json({ count })),
  genDesc: (count) => req('/questions/descriptive', json({ count })),
  createTest: (mcq_count, descriptive_count) => req('/tests', json({ mcq_count, descriptive_count })),
  getTest: (id) => req(`/tests/${id}`),
  saveAttempt: (id, answers) => req(`/tests/${id}/attempt`, json({ answers })),
  submit: (id, answers) => req(`/tests/${id}/submit`, json({ answers })),
  result: (id) => req(`/tests/${id}/result`),
}
