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

const adminHeaders = () => ({ 'X-Admin-Password': sessionStorage.getItem('adminpw') || '' })

export const api = {
  documents: (userId) => req(`/documents?user_id=${userId}`),
  upload: (files, userId) => {
    const fd = new FormData()
    for (const f of files) fd.append('files', f)
    fd.append('user_id', userId)
    return req('/documents/upload', { method: 'POST', body: fd })
  },
  ingest: (userId) => req(`/documents/ingest?user_id=${userId}`, { method: 'POST' }),
  ingestOne: (id) => req(`/documents/${id}/ingest`, { method: 'POST' }),
  deleteDoc: (id) => req(`/documents/${id}`, { method: 'DELETE' }),
  genMcq: (count, user_id) => req('/questions/mcq', json({ count, user_id })),
  genDesc: (count, user_id) => req('/questions/descriptive', json({ count, user_id })),
  createTest: (mcq_count, descriptive_count, user_id) =>
    req('/tests', json({ mcq_count, descriptive_count, user_id })),
  getTest: (id) => req(`/tests/${id}`),
  saveAttempt: (id, answers, user_id) => req(`/tests/${id}/attempt`, json({ answers, user_id })),
  submit: (id, answers, user_id) => req(`/tests/${id}/submit`, json({ answers, user_id })),
  result: (id) => req(`/tests/${id}/result`),
  users: () => req('/users'),
  createUser: (body) => req('/users', json(body)),
  login: (email, password) => req('/users/login', json({ email, password })),
  userTests: (id) => req(`/users/${id}/tests`),
  adminCheck: (pw) => req('/admin/_check', { headers: { 'X-Admin-Password': pw } }),
  adminList: (e) => req(`/admin/${e}`, { headers: adminHeaders() }),
  adminCreate: (e, data) => req(`/admin/${e}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', ...adminHeaders() }, body: JSON.stringify(data),
  }),
  adminDelete: (e, id) => req(`/admin/${e}/${id}`, { method: 'DELETE', headers: adminHeaders() }),
  adminReset: () => req('/admin/reset', { method: 'POST', headers: adminHeaders() }),
}
