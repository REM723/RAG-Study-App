import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useUser } from '../user.jsx'
import { api } from '../api'

export default function Dashboard() {
  const { user } = useUser()
  const [tests, setTests] = useState([])

  useEffect(() => { api.userTests(user.id).then(setTests).catch(() => {}) }, [user.id])

  const done = tests.filter((t) => t.submitted)
  const avg = done.length
    ? Math.round((done.reduce((s, t) => s + (t.score / (t.max || 1)), 0) / done.length) * 100)
    : null

  return (
    <div>
      <div className="banner" style={{ backgroundImage: 'url(/img/study.jpg)' }}>
        <h1>Welcome back, {user.name}</h1>
        <p>{tests.length} test{tests.length === 1 ? '' : 's'} · {done.length} completed
          {avg !== null ? ` · ${avg}% average` : ''}</p>
      </div>
      <p><Link to="/build" className="btn" style={{ textDecoration: 'none', display: 'inline-block' }}>+ Build a new test</Link></p>

      <details className="card howcard" open={tests.length === 0}>
        <summary>How it works</summary>
        <p className="muted" style={{ margin: '.4rem 0 1rem' }}>
          Go from your notes to a graded practice test in five steps.
        </p>
        <div className="steps">
          <div className="step">
            <div className="step__num">1</div>
            <div className="step__body">
              <div className="step__title">📄 Add your material</div>
              <div className="step__desc">Upload PDFs on the <Link to="/documents">Documents</Link> page and hit <b>Ingest</b> — the app reads and indexes them so it understands your content.</div>
            </div>
          </div>
          <div className="step">
            <div className="step__num">2</div>
            <div className="step__body">
              <div className="step__title">✨ Generate questions</div>
              <div className="step__desc">On <Link to="/generate">Generate</Link>, create multiple-choice and descriptive questions drawn straight from your material — each one cites the page it came from.</div>
            </div>
          </div>
          <div className="step">
            <div className="step__num">3</div>
            <div className="step__body">
              <div className="step__title">🧩 Build a test</div>
              <div className="step__desc">On <Link to="/build">Build Test</Link>, pick how many of each type you want and we'll assemble a test from your question bank.</div>
            </div>
          </div>
          <div className="step">
            <div className="step__num">4</div>
            <div className="step__body">
              <div className="step__title">✍️ Take it</div>
              <div className="step__desc">Answer at your own pace — your progress saves automatically. Submit when you're ready.</div>
            </div>
          </div>
          <div className="step">
            <div className="step__num">5</div>
            <div className="step__body">
              <div className="step__title">📊 Review your results</div>
              <div className="step__desc">See your score, a section-by-section breakdown, correct answers, point-by-point feedback, and the source behind every question on the <Link to="/results">Results</Link> page.</div>
            </div>
          </div>
        </div>
        <p className="muted" style={{ marginTop: '1rem' }}>🔒 Everything stays private to your account — never shared with other users.</p>
      </details>

      <h2>Your tests &amp; scores</h2>
      {tests.length === 0 ? <p>No tests yet — build one to get started.</p> : (
        <table>
          <thead><tr><th>Test</th><th>Questions</th><th>Status</th><th>Score</th><th></th></tr></thead>
          <tbody>
            {tests.map((t) => (
              <tr key={t.id}>
                <td>Test {t.seq}</td>
                <td>{t.question_count}</td>
                <td>{t.submitted ? 'submitted' : 'pending'}</td>
                <td>{t.submitted ? `${t.score} / ${t.max}` : '—'}</td>
                <td>
                  {t.submitted
                    ? <Link to={`/tests/${t.id}/result`}>View result</Link>
                    : <Link to={`/tests/${t.id}`}>Take test</Link>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
