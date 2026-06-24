import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUser } from '../user.jsx'
import { api } from '../api'

export default function Upload() {
  const { user } = useUser()
  const [files, setFiles] = useState([])
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()

  const pick = (list) => {
    const arr = Array.from(list).filter((f) => f.name.toLowerCase().endsWith('.pdf'))
    setErr(arr.length > 5 ? 'Max 5 files; extras ignored.' : null)
    setFiles(arr.slice(0, 5))
  }

  const submit = async () => {
    setErr(null); setMsg(null); setBusy(true)
    try {
      const r = await api.upload(files, user.id)
      setMsg(`Uploaded ${r.uploaded.length} file(s).`)
      setFiles([])
    } catch (e) { setErr(e.message) }
    setBusy(false)
  }

  return (
    <div>
      <h1>Upload PDFs</h1>
      <div
        className="drop"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); pick(e.dataTransfer.files) }}
      >
        Drag &amp; drop 1–5 PDFs here, or{' '}
        <input type="file" multiple accept="application/pdf" onChange={(e) => pick(e.target.files)} />
      </div>
      {files.length > 0 && <ul>{files.map((f) => <li key={f.name}>{f.name}</li>)}</ul>}
      <button disabled={!files.length || busy} onClick={submit}>Upload</button>
      {msg && (
        <p className="ok">
          {msg} <button onClick={() => nav('/documents')}>Go to Documents →</button>
        </p>
      )}
      {err && <p className="err">{err}</p>}
    </div>
  )
}
