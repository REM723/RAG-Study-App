import { useState } from 'react'
import { useUser } from '../user.jsx'
import { api } from '../api'

export default function Login() {
  const { login } = useUser()
  const [mode, setMode] = useState('login') // 'login' | 'signup'
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async () => {
    setErr(null); setBusy(true)
    try {
      if (mode === 'signup') {
        if (!form.name || !form.email || !form.password) throw new Error('All fields required')
        login(await api.createUser(form))
      } else {
        if (!form.email || !form.password) throw new Error('Email and password required')
        login(await api.login(form.email, form.password))
      }
    } catch (e) { setErr(e.message); setBusy(false) }
  }

  return (
    <div className="auth">
      <div className="auth__form">
        <div className="brand" style={{ fontSize: '1.15rem', marginBottom: '.4rem' }}>
          <img src="/img/logo.svg" alt="" width="30" height="30" /> StudyRAG
        </div>
        <h1 style={{ marginTop: '.4rem' }}>
          {mode === 'login' ? 'Welcome back' : 'Create your account'}
        </h1>
        <p className="muted" style={{ marginTop: '-.4rem', marginBottom: '1.4rem' }}>
          {mode === 'login'
            ? 'Log in to your study workspace.'
            : 'Upload your books, generate questions, take tests — all from your own material.'}
        </p>

        <div className="stack">
          {mode === 'signup' && (
            <input placeholder="Your name" value={form.name} onChange={set('name')} />
          )}
          <input placeholder="Email" type="email" value={form.email} onChange={set('email')} />
          <input placeholder="Password" type="password" value={form.password} onChange={set('password')}
            onKeyDown={(e) => e.key === 'Enter' && submit()} />
          <button disabled={busy} onClick={submit}>
            {busy ? '…' : mode === 'login' ? 'Log in →' : 'Create account →'}
          </button>
        </div>

        <p className="muted" style={{ marginTop: '.9rem' }}>
          {mode === 'login' ? "No account yet? " : 'Already have an account? '}
          <a href="#" onClick={(e) => { e.preventDefault(); setErr(null); setMode(mode === 'login' ? 'signup' : 'login') }}>
            {mode === 'login' ? 'Create one' : 'Log in'}
          </a>
        </p>
        {err && <p className="err">{err}</p>}
        <p className="muted" style={{ marginTop: '1rem' }}><a href="/admin">Admin panel →</a></p>
      </div>

      <div className="auth__art" style={{ backgroundImage: 'url(/img/hero.jpg)' }}>
        <div className="cap">
          <h3>Study smarter</h3>
          <p>Grounded questions with sources — every answer traces back to your pages.</p>
        </div>
      </div>
    </div>
  )
}
