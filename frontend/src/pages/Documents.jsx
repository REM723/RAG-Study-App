import { useEffect, useState } from 'react'
import { useUser } from '../user.jsx'
import { api } from '../api'

export default function Documents() {
  const { user } = useUser()
  const [docs, setDocs] = useState([])
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)

  const load = async () => {
    try { setDocs(await api.documents(user.id)) } catch (e) { setErr(e.message) }
  }

  useEffect(() => { load() }, [])

  // poll while anything is still processing
  useEffect(() => {
    if (!docs.some((d) => d.status === 'processing')) return
    const t = setInterval(load, 2000)
    return () => clearInterval(t)
  }, [docs])

  const ingest = async () => {
    setErr(null); setBusy(true)
    try { await api.ingest(user.id); await load() } catch (e) { setErr(e.message) }
    setBusy(false)
  }

  const remove = async (d) => {
    if (!window.confirm(`Delete ${d.filename}?`)) return
    setErr(null)
    try { await api.deleteDoc(d.id); await load() } catch (e) { setErr(e.message) }
  }

  return (
    <div>
      <h1>Documents</h1>
      <button disabled={busy} onClick={ingest}>Ingest into Vector Store</button>
      {err && <p className="err">{err}</p>}
      {docs.length ? (
        <table>
          <thead><tr><th>File</th><th>Status</th><th>Chunks</th><th></th></tr></thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id}>
                <td>{d.filename}</td>
                <td className={`st-${d.status}`}>{d.status}{d.error ? `: ${d.error}` : ''}</td>
                <td>{d.chunks}</td>
                <td><button onClick={() => remove(d)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
          <img src="/img/books.jpg" alt="" style={{ width: '180px', height: '120px', objectFit: 'cover', borderRadius: '12px', opacity: .9 }} />
          <p className="muted">No documents yet — head to <strong>Upload</strong> to add your PDFs, then ingest them here.</p>
        </div>
      )}
    </div>
  )
}
