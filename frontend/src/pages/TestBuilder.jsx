import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

export default function TestBuilder() {
  const [mcq, setMcq] = useState(3)
  const [desc, setDesc] = useState(1)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()

  const create = async () => {
    setErr(null); setBusy(true)
    try {
      const t = await api.createTest(Number(mcq), Number(desc))
      nav(`/tests/${t.id}`)
    } catch (e) { setErr(e.message); setBusy(false) }
  }

  return (
    <div>
      <h1>Build a Test</h1>
      <label>MCQ count <input type="number" min="0" value={mcq} onChange={(e) => setMcq(e.target.value)} /></label>
      <label>Descriptive count <input type="number" min="0" value={desc} onChange={(e) => setDesc(e.target.value)} /></label>
      <button disabled={busy} onClick={create}>Create &amp; Start</button>
      {err && <p className="err">{err}</p>}
    </div>
  )
}
