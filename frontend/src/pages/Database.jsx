import { useEffect, useState } from 'react'
import { api } from '../api'

// Editable fields per entity (id + created_at are server-set, shown in the table only).
// t: 'number' | 'json' | undefined(text). user_id renders a dropdown of users.
const ENTITIES = [
  { name: 'users', label: 'Users', fields: [{ k: 'name' }, { k: 'email' }, { k: 'role' }] },
  { name: 'documents', label: 'Documents', fields: [
    { k: 'user_id', t: 'user' }, { k: 'filename' }, { k: 'file_size', t: 'number' }, { k: 'status' }] },
  { name: 'chunks', label: 'Chunks', fields: [
    { k: 'document_id', t: 'number' }, { k: 'text' }, { k: 'page_number', t: 'number' },
    { k: 'chapter' }, { k: 'embedding_ref' }] },
  { name: 'questions', label: 'Questions', fields: [
    { k: 'type' }, { k: 'question' }, { k: 'options', t: 'json' }, { k: 'answer' },
    { k: 'source_file' }, { k: 'source_page', t: 'number' }] },
  { name: 'rubrics', label: 'Rubrics', fields: [
    { k: 'question_id', t: 'number' }, { k: 'scoring_points', t: 'json' }, { k: 'max_marks', t: 'number' }] },
  { name: 'tests', label: 'Tests', fields: [
    { k: 'user_id', t: 'user' }, { k: 'question_ids', t: 'json' }, { k: 'question_count', t: 'number' },
    { k: 'status' }] },
  { name: 'attempts', label: 'Attempts', fields: [
    { k: 'test_id', t: 'number' }, { k: 'user_id', t: 'user' }, { k: 'answers', t: 'json' },
    { k: 'score', t: 'number' }] },
  { name: 'evaluations', label: 'Evaluations', fields: [
    { k: 'attempt_id', t: 'number' }, { k: 'per_question_score', t: 'json' }, { k: 'feedback' },
    { k: 'total_score', t: 'number' }] },
]

const cell = (v) => (v !== null && typeof v === 'object' ? JSON.stringify(v) : String(v ?? ''))

function Entity({ entity, users, onUsersChange }) {
  const [rows, setRows] = useState([])
  const [form, setForm] = useState({})
  const [err, setErr] = useState(null)

  const load = () => api.adminList(entity.name).then(setRows).catch((e) => setErr(e.message))
  useEffect(() => { load() }, [])

  const add = async () => {
    setErr(null)
    const payload = {}
    try {
      for (const f of entity.fields) {
        const raw = form[f.k]
        if (raw === undefined || raw === '') continue
        payload[f.k] = f.t === 'json' ? JSON.parse(raw) : raw
      }
    } catch { setErr('Invalid JSON in one of the fields'); return }
    try {
      await api.adminCreate(entity.name, payload)
      setForm({})
      await load()
      if (entity.name === 'users') onUsersChange()
    } catch (e) { setErr(e.message) }
  }

  const remove = async (id) => {
    try { await api.adminDelete(entity.name, id); await load(); if (entity.name === 'users') onUsersChange() }
    catch (e) { setErr(e.message) }
  }

  const cols = rows.length ? Object.keys(rows[0]) : ['id', ...entity.fields.map((f) => f.k)]

  return (
    <details className="card">
      <summary><strong>{entity.label}</strong> ({rows.length})</summary>

      <div className="adminform">
        {entity.fields.map((f) => f.t === 'user' ? (
          <select key={f.k} value={form[f.k] || ''} onChange={(e) => setForm({ ...form, [f.k]: e.target.value })}>
            <option value="">{f.k}…</option>
            {users.map((u) => <option key={u.id} value={u.id}>{u.id}: {u.name}</option>)}
          </select>
        ) : (
          <input
            key={f.k}
            type={f.t === 'number' ? 'number' : 'text'}
            placeholder={f.t === 'json' ? `${f.k} (JSON)` : f.k}
            value={form[f.k] || ''}
            onChange={(e) => setForm({ ...form, [f.k]: e.target.value })}
          />
        ))}
        <button onClick={add}>Add</button>
      </div>
      {err && <p className="err">{err}</p>}

      {rows.length > 0 && (
        <table>
          <thead><tr>{cols.map((c) => <th key={c}>{c}</th>)}<th></th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                {cols.map((c) => <td key={c}>{cell(r[c])}</td>)}
                <td><button onClick={() => remove(r.id)}>✕</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </details>
  )
}

function AdminGate({ onAuthed }) {
  const [pw, setPw] = useState('')
  const [err, setErr] = useState(null)
  const tryPw = async () => {
    setErr(null)
    try {
      await api.adminCheck(pw)
      sessionStorage.setItem('adminpw', pw)
      onAuthed()
    } catch { setErr('Invalid admin password') }
  }
  return (
    <div className="card" style={{ maxWidth: 360, margin: '3rem auto', textAlign: 'center' }}>
      <h2 style={{ marginTop: 0 }}>Admin access</h2>
      <p className="muted">Enter the admin password to manage the database.</p>
      <input type="password" placeholder="Admin password" value={pw}
        onChange={(e) => setPw(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && tryPw()}
        style={{ width: '100%', marginBottom: '.6rem' }} />
      <button onClick={tryPw} style={{ width: '100%' }}>Unlock</button>
      {err && <p className="err">{err}</p>}
    </div>
  )
}

export default function Database() {
  const [authed, setAuthed] = useState(false)
  const [users, setUsers] = useState([])
  const loadUsers = () => api.adminList('users').then(setUsers).catch(() => {})

  useEffect(() => {
    const pw = sessionStorage.getItem('adminpw')
    if (!pw) return
    api.adminCheck(pw).then(() => setAuthed(true)).catch(() => sessionStorage.removeItem('adminpw'))
  }, [])

  // lock the panel whenever you leave the page (unmount) — must re-enter the password next time
  useEffect(() => () => sessionStorage.removeItem('adminpw'), [])

  useEffect(() => { if (authed) loadUsers() }, [authed])

  if (!authed) return <AdminGate onAuthed={() => setAuthed(true)} />

  const reset = async () => {
    if (!window.confirm('Reset EVERYTHING — all tables, the vector index, and uploaded PDFs. This cannot be undone. Continue?')) return
    try {
      await api.adminReset()
      localStorage.removeItem('user')  // logged-in user was wiped too
      window.location.reload()
    } catch (e) { alert(e.message) }
  }

  return (
    <div>
      <h1>Database <button className="danger" onClick={reset}>Reset all</button></h1>
      {ENTITIES.map((e) => (
        <Entity key={e.name} entity={e} users={users} onUsersChange={loadUsers} />
      ))}
    </div>
  )
}
