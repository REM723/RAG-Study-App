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
