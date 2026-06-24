import { Routes, Route, Link, Navigate } from 'react-router-dom'
import Upload from './pages/Upload.jsx'
import Documents from './pages/Documents.jsx'
import Generate from './pages/Generate.jsx'
import TestBuilder from './pages/TestBuilder.jsx'
import Attempt from './pages/Attempt.jsx'
import Results from './pages/Results.jsx'

export default function App() {
  return (
    <div className="app">
      <nav>
        <Link to="/upload">Upload</Link>
        <Link to="/documents">Documents</Link>
        <Link to="/generate">Generate</Link>
        <Link to="/build">Build Test</Link>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<Navigate to="/upload" />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/generate" element={<Generate />} />
          <Route path="/build" element={<TestBuilder />} />
          <Route path="/tests/:id" element={<Attempt />} />
          <Route path="/tests/:id/result" element={<Results />} />
        </Routes>
      </main>
    </div>
  )
}
