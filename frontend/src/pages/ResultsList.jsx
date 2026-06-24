import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useUser } from '../user.jsx'
import { api } from '../api'

export default function ResultsList() {
  const { user } = useUser()
  const [tests, setTests] = useState([])

  useEffect(() => { api.userTests(user.id).then(setTests).catch(() => {}) }, [user.id])

  const done = tests.filter((t) => t.submitted)

  return (
    <div>
      <h1>Results</h1>
      {done.length === 0 ? (
        <p className="muted">No completed tests yet. Build and take a test to see your evaluation here.</p>
      ) : (
        <table>
          <thead><tr><th>Test</th><th>Questions</th><th>Score</th><th>%</th><th></th></tr></thead>
          <tbody>
            {done.map((t) => (
              <tr key={t.id}>
                <td>Test {t.seq}</td>
                <td>{t.question_count}</td>
                <td>{t.score} / {t.max}</td>
                <td>{t.max ? Math.round((t.score / t.max) * 100) : 0}%</td>
                <td><Link to={`/tests/${t.id}/result`}>View evaluation</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
