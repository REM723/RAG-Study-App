import { Routes, Route, Link, Navigate, useLocation } from 'react-router-dom'
import { useUser } from './user.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Upload from './pages/Upload.jsx'
import Documents from './pages/Documents.jsx'
import Generate from './pages/Generate.jsx'
import TestBuilder from './pages/TestBuilder.jsx'
import Attempt from './pages/Attempt.jsx'
import Results from './pages/Results.jsx'
import Database from './pages/Database.jsx'

export default function App() {
  const { user, logout } = useUser()
  const isAdmin = useLocation().pathname.startsWith('/admin')
  const guard = (el) => (user ? el : <Navigate to="/login" replace />)

  return (
    <div className="app">
      {isAdmin ? (
        <nav>
          <span className="brand"><img src="/img/logo.svg" alt="" />Admin Panel</span>
          <Link to="/" style={{ marginLeft: 'auto' }}>← Back to app</Link>
        </nav>
      ) : user ? (
        <nav>
          <Link to="/" className="brand"><img src="/img/logo.svg" alt="" />StudyRAG</Link>
          <Link to="/upload">Upload</Link>
          <Link to="/documents">Documents</Link>
          <Link to="/generate">Generate</Link>
          <Link to="/build">Build Test</Link>
          <span style={{ marginLeft: 'auto', color: 'var(--muted)', fontSize: '.9rem' }}>
            {user.name} · {user.role}
          </span>
          <button className="ghost" onClick={logout}>Logout</button>
        </nav>
      ) : null}

      <main>
        <Routes>
          <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
          <Route path="/admin" element={<Database />} />
          <Route path="/" element={guard(<Dashboard />)} />
          <Route path="/upload" element={guard(<Upload />)} />
          <Route path="/documents" element={guard(<Documents />)} />
          <Route path="/generate" element={guard(<Generate />)} />
          <Route path="/build" element={guard(<TestBuilder />)} />
          <Route path="/tests/:id" element={guard(<Attempt />)} />
          <Route path="/tests/:id/result" element={guard(<Results />)} />
        </Routes>
      </main>
    </div>
  )
}
