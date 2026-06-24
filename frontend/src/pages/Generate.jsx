import { useState } from 'react'
import { useUser } from '../user.jsx'
import { api } from '../api'

export default function Generate() {
  const { user } = useUser()
  const [mcqN, setMcqN] = useState(3)
  const [descN, setDescN] = useState(2)
  const [mcqs, setMcqs] = useState([])
  const [descs, setDescs] = useState([])
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)

  const run = async () => {
    setErr(null); setBusy(true); setMcqs([]); setDescs([])
    try {
      if (Number(mcqN) > 0) setMcqs(await api.genMcq(Number(mcqN), user.id))
      if (Number(descN) > 0) setDescs(await api.genDesc(Number(descN), user.id))
    } catch (e) { setErr(e.message) }
    setBusy(false)
  }

  const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  // ponytail: browser print-to-PDF instead of a server-side PDF lib
  const savePdf = () => {
    const parts = []

    if (mcqs.length) {
      const qs = mcqs.map((q, i) =>
        `<div class="q"><p><b>Q${i + 1}.</b> ${esc(q.question)}</p>` +
        `<ol type="A">${q.options.map((o) => `<li>${esc(o)}</li>`).join('')}</ol></div>`).join('')
      const key = mcqs.map((q, i) => `<li>Q${i + 1}: ${esc(q.answer)}</li>`).join('')
      parts.push(`<h2>Multiple Choice</h2>${qs}<h3>Answer Key</h3><ol>${key}</ol>`)
    }

    if (descs.length) {
      const qs = descs.map((q, i) => `<div class="q"><p><b>Q${i + 1}.</b> ${esc(q.question)}</p></div>`).join('')
      const ans = descs.map((q, i) =>
        `<div class="q"><p><b>Q${i + 1}.</b></p><ul>${q.rubric.map((p) => `<li>${esc(p)}</li>`).join('')}</ul></div>`).join('')
      parts.push(`<h2>Descriptive</h2>${qs}<h3>Model Answers</h3>${ans}`)
    }

    const w = window.open('', '_blank')
    w.document.write(
      `<html><head><title>Questions</title><style>body{font-family:sans-serif;padding:24px;color:#111}` +
      `.q{margin-bottom:14px}ol,ul{margin:.25rem 0}h2{margin-top:28px}h3{margin-top:20px}</style></head><body>` +
      `<h1>Generated Questions</h1>${parts.join('')}</body></html>`)
    w.document.close()
    w.focus()
    w.print()
  }

  return (
    <div>
      <h1>Generate Questions</h1>
      <label>MCQ <input type="number" min="0" value={mcqN} onChange={(e) => setMcqN(e.target.value)} /></label>
      <label>Descriptive <input type="number" min="0" value={descN} onChange={(e) => setDescN(e.target.value)} /></label>
      <button disabled={busy} onClick={run}>{busy ? 'Generating…' : 'Generate'}</button>
      {(mcqs.length > 0 || descs.length > 0) && (
        <button onClick={savePdf} style={{ marginLeft: '.5rem' }}>Save as PDF</button>
      )}
      {err && <p className="err">{err}</p>}

      {mcqs.length > 0 && (
        <section>
          <h2>Multiple Choice</h2>
          {mcqs.map((q, i) => (
            <div key={q.id} className="card">
              <p><strong>Q{i + 1}.</strong> {q.question}</p>
              <ol type="A">
                {q.options.map((o, j) => <li key={j} className={o === q.answer ? 'correct' : ''}>{o}</li>)}
              </ol>
              {q.explanation && <p className="muted">{q.explanation}</p>}
              <p className="src">Source: {q.source_file} · p.{q.source_page}</p>
            </div>
          ))}
        </section>
      )}

      {descs.length > 0 && (
        <section>
          <h2>Descriptive</h2>
          {descs.map((q, i) => (
            <div key={q.id} className="card">
              <p><strong>Q{i + 1}.</strong> {q.question}</p>
              <ul>{q.rubric.map((p, j) => <li key={j}>{p}</li>)}</ul>
              <p className="src">Source: {q.source_file} · p.{q.source_page}</p>
            </div>
          ))}
        </section>
      )}
    </div>
  )
}
