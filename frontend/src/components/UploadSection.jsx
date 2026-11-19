import { useRef, useState } from "react";
import { formatDate } from "../utils";

const MAX_SIZE = 5 * 1024 * 1024;
const ALLOWED = ["pdf", "txt"];

export default function UploadSection({ documents, onUpload, onDelete }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [problems, setProblems] = useState([]);

  async function handleFiles(fileList) {
    const files = Array.from(fileList);
    if (files.length === 0) return;

    setBusy(true);
    setProblems([]);
    const found = [];

    for (const file of files) {
      const ext = file.name.split(".").pop().toLowerCase();
      if (!ALLOWED.includes(ext)) {
        found.push(`${file.name}: only PDF or TXT files are allowed.`);
        continue;
      }
      if (file.size > MAX_SIZE) {
        found.push(`${file.name}: file is larger than 5 MB.`);
        continue;
      }
      try {
        await onUpload(file);
      } catch (err) {
        found.push(`${file.name}: ${err.message}`);
      }
    }

    setProblems(found);
    setBusy(false);
    if (inputRef.current) inputRef.current.value = ""; // wahi file dobara chun sakein
  }

  async function handleDelete(doc) {
    if (!window.confirm(`Delete "${doc.filename}"?`)) return;
    try {
      setProblems([]);
      await onDelete(doc.id);
    } catch (err) {
      setProblems([err.message]);
    }
  }

  return (
    <section className="sec" id="upload">
      <div className="card">
        <h2>Upload documents</h2>
        <p className="sub">PDF or TXT, up to 5 MB each.</p>

        <div
          className={`drop ${dragging ? "active" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            handleFiles(e.dataTransfer.files);
          }}
        >
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2F7D6D"
               strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M12 16V4M7 9l5-5 5 5M4 20h16" />
          </svg>
          <p>Drag files here, or choose from your computer</p>
          <button className="btn" onClick={() => inputRef.current?.click()} disabled={busy}>
            {busy ? "Uploading..." : "Choose files"}
          </button>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.txt"
            multiple
            hidden
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>

        {problems.length > 0 && (
          <div className="error" style={{ marginTop: 0, marginBottom: 16 }}>
            {problems.map((p, i) => <div key={i}>{p}</div>)}
          </div>
        )}

        <div className="tw">
          <table>
            <thead>
              <tr><th>Name</th><th>Type</th><th>Words</th><th>Uploaded</th><th></th></tr>
            </thead>
            <tbody>
              {documents.map((d) => (
                <tr key={d.id}>
                  <td>{d.filename}</td>
                  <td>{d.file_type.toUpperCase()}</td>
                  <td>{d.word_count.toLocaleString()}</td>
                  <td>{formatDate(d.uploaded_at)}</td>
                  <td><button className="btn2" onClick={() => handleDelete(d)}>Delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
          {documents.length === 0 && <div className="empty">No documents uploaded yet.</div>}
        </div>
      </div>
    </section>
  );
}