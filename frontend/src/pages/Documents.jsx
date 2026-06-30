import { useEffect, useState } from 'react'
import { useUser } from '../user.jsx'
import { api } from '../api'

export default function Documents() {
  const { user } = useUser()
  const [docs, setDocs] = useState([])
  const [files, setFiles] = useState([])
  const [msg, setMsg] = useState(null)
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

  const pick = (list) => {
    const arr = Array.from(list).filter((f) => f.name.toLowerCase().endsWith('.pdf'))
    setErr(arr.length > 5 ? 'Max 5 files; extras ignored.' : null)
    setFiles(arr.slice(0, 5))
  }

  const upload = async () => {
    setErr(null); setMsg(null); setBusy(true)
    try {
      const r = await api.upload(files, user.id)
      setMsg(`Uploaded ${r.uploaded.length} file(s). Click “Ingest” next to each to index it.`)
      setFiles([])
      await load()
    } catch (e) { setErr(e.message) }
    setBusy(false)
  }

  const ingestOne = async (d) => {
    setErr(null); setMsg(null)
    try { await api.ingestOne(d.id); await load() } catch (e) { setErr(e.message) }
  }

  const remove = async (d) => {
    if (!window.confirm(`Delete ${d.filename}?`)) return
    setErr(null)
    try { await api.deleteDoc(d.id); await load() } catch (e) { setErr(e.message) }
  }

  return (
    <div>
      <h1>Documents</h1>

      <div
        className="drop"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); pick(e.dataTransfer.files) }}
      >
        Drag &amp; drop 1–5 PDFs here, or{' '}
        <input type="file" multiple accept="application/pdf" onChange={(e) => pick(e.target.files)} />
      </div>
      {files.length > 0 && <ul>{files.map((f) => <li key={f.name}>{f.name}</li>)}</ul>}
      <div style={{ display: 'flex', gap: '.5rem', alignItems: 'center', flexWrap: 'wrap', marginTop: '1rem' }}>
        <button disabled={!files.length || busy} onClick={upload}>Upload</button>
      </div>
      {msg && <p className="ok">{msg}</p>}
      {err && <p className="err">{err}</p>}

      <h2>Your documents</h2>
      {docs.length ? (
        <table>
          <thead><tr><th>File</th><th>Status</th><th>Chunks</th><th></th></tr></thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id}>
                <td>{d.filename}</td>
                <td className={`st-${d.status}`}>{d.status}{d.error ? `: ${d.error}` : ''}</td>
                <td>{d.chunks}</td>
                <td style={{ display: 'flex', gap: '.5rem' }}>
                  {d.status !== 'completed' && (
                    <button disabled={d.status === 'processing'} onClick={() => ingestOne(d)}>
                      {d.status === 'processing' ? 'Ingesting…' : 'Ingest'}
                    </button>
                  )}
                  <button className="ghost" onClick={() => remove(d)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
          <img src="/img/books.jpg" alt="" style={{ width: '180px', height: '120px', objectFit: 'cover', borderRadius: '12px', opacity: .9 }} />
          <p className="muted">No documents yet — drop your PDFs above and ingest them.</p>
        </div>
      )}
    </div>
  )
}
