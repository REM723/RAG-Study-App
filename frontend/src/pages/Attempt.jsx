import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'

export default function Attempt() {
  const { id } = useParams()
  const [test, setTest] = useState(null)
  const [answers, setAnswers] = useState({})
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState(false)
  const nav = useNavigate()
  const timer = useRef()

  useEffect(() => { api.getTest(id).then(setTest).catch((e) => setErr(e.message)) }, [id])

  const setAns = (qid, val) => {
    const next = { ...answers, [qid]: val }
    setAnswers(next); setSaved(false)
    clearTimeout(timer.current)  // debounced autosave
    timer.current = setTimeout(() => {
      api.saveAttempt(id, next).then(() => setSaved(true)).catch(() => {})
    }, 800)
  }

  const submit = async () => {
    setBusy(true); setErr(null)
    try { await api.submit(id, answers); nav(`/tests/${id}/result`) }
    catch (e) { setErr(e.message); setBusy(false) }
  }

  if (err) return <p className="err">{err}</p>
  if (!test) return <p>Loading…</p>

  return (
    <div>
      <h1>Test #{test.id}</h1>
      {test.questions.map((q, i) => (
        <div key={q.id} className="card">
          <p><strong>{i + 1}.</strong> {q.question}</p>
          {q.type === 'mcq'
            ? q.options.map((o, j) => (
              <label key={j} className="opt">
                <input
                  type="radio"
                  name={`q${q.id}`}
                  checked={answers[q.id] === o}
                  onChange={() => setAns(q.id, o)}
                /> {o}
              </label>))
            : <textarea rows="4" value={answers[q.id] || ''} onChange={(e) => setAns(q.id, e.target.value)} />}
          <p className="src">Source: {q.source_file} · p.{q.source_page}</p>
        </div>
      ))}
      <button disabled={busy} onClick={submit}>Submit</button>
      <span className="muted">{saved ? ' progress saved' : ''}</span>
      {err && <p className="err">{err}</p>}
    </div>
  )
}
