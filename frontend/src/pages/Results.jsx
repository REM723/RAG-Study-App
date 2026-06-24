import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api'

export default function Results() {
  const { id } = useParams()
  const [r, setR] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => { api.result(id).then(setR).catch((e) => setErr(e.message)) }, [id])

  const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  // ponytail: browser print-to-PDF, same as the Generate page
  const savePdf = () => {
    const qs = r.questions.map((q, i) => {
      const detail = q.type === 'mcq'
        ? `<p class="${q.correct ? 'ok' : 'bad'}">Correct: ${esc(q.correct_answer)}` +
          `${q.explanation ? ` — ${esc(q.explanation)}` : ''}</p>`
        : `<ul>${q.rubric.map((pt) =>
            `<li class="${pt.covered ? 'ok' : 'bad'}">${pt.covered ? '✓' : '✗'} ${esc(pt.point)}</li>`).join('')}</ul>` +
          `${q.feedback ? `<p class="muted">${esc(q.feedback)}</p>` : ''}`
      return `<div class="q"><p><b>${i + 1}.</b> ${esc(q.question)} — <b>${q.marks}/${q.max}</b></p>` +
        `<p>Your answer: ${q.your_answer ? esc(q.your_answer) : '<i>(blank)</i>'}</p>${detail}` +
        `<p class="src">Source: ${esc(q.source_file)} · p.${q.source_page}</p></div>`
    }).join('')
    const w = window.open('', '_blank')
    w.document.write(
      `<html><head><title>Test #${id} Result</title><style>body{font-family:sans-serif;padding:24px;color:#111}` +
      `.q{margin-bottom:16px}ul{margin:.25rem 0}.score{font-size:1.3rem;font-weight:700}` +
      `.ok{color:#16a34a}.bad{color:#dc2626}.muted{color:#666}.src{color:#888;font-size:.85rem}</style></head><body>` +
      `<h1>Test #${id} Result</h1><p class="score">Score: ${r.total} / ${r.max}</p>` +
      `<p>MCQ: ${r.sections.mcq.score}/${r.sections.mcq.max} · ` +
      `Descriptive: ${r.sections.descriptive.score}/${r.sections.descriptive.max}</p>${qs}</body></html>`)
    w.document.close()
    w.focus()
    w.print()
  }

  if (err) return <p className="err">{err}</p>
  if (!r) return <p>Loading…</p>

  return (
    <div>
      <h1>Result <button onClick={savePdf}>Save as PDF</button></h1>
      <p className="score">Score: {r.total} / {r.max}</p>
      <p>
        MCQ: {r.sections.mcq.score}/{r.sections.mcq.max} ·{' '}
        Descriptive: {r.sections.descriptive.score}/{r.sections.descriptive.max}
      </p>
      {r.questions.map((q, i) => (
        <div key={q.id} className="card">
          <p><strong>{i + 1}.</strong> {q.question} — <strong>{q.marks}/{q.max}</strong></p>
          <p>Your answer: {q.your_answer || <em>(blank)</em>}</p>
          {q.type === 'mcq'
            ? <p className={q.correct ? 'ok' : 'err'}>
                Correct: {q.correct_answer}{q.explanation ? ` — ${q.explanation}` : ''}
              </p>
            : <>
                <ul>
                  {q.rubric.map((pt, j) => (
                    <li key={j} className={pt.covered ? 'ok' : 'err'}>
                      {pt.covered ? '✓' : '✗'} {pt.point}
                    </li>
                  ))}
                </ul>
                {q.feedback && <p className="muted">{q.feedback}</p>}
              </>}
          <p className="src">Source: {q.source_file} · p.{q.source_page}</p>
        </div>
      ))}
    </div>
  )
}
