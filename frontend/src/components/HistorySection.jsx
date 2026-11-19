import { useState } from "react";
import { formatDate } from "../utils";

export default function HistorySection({ history, onOpen, onDelete }) {
  const [query, setQuery] = useState("");
  const q = query.trim().toLowerCase();

  const rows = history.filter(
    (h) => !q || `${h.source_filename} ${h.target_filenames}`.toLowerCase().includes(q)
  );

  async function handleDelete(id) {
    if (window.confirm("Delete this comparison from history?")) await onDelete(id);
  }

  return (
    <section className="sec" id="history">
      <div className="card">
        <div className="head-row">
          <div>
            <h2>History</h2>
            <p className="sub" style={{ margin: 0 }}>Your saved comparisons.</p>
          </div>
          <div style={{ width: 280, maxWidth: "100%" }}>
            <label htmlFor="search">Search</label>
            <input id="search" type="text" placeholder="Search by file name"
                   value={query} onChange={(e) => setQuery(e.target.value)} />
          </div>
        </div>

        <div className="tw">
          <table>
            <thead>
              <tr><th>Date</th><th>Mode</th><th>Documents</th><th>Top score</th><th></th></tr>
            </thead>
            <tbody>
              {rows.map((h) => (
                <tr key={h.id}>
                  <td>{formatDate(h.created_at)}</td>
                  <td>{h.mode === "pair" ? "Pair" : "One vs Many"}</td>
                  <td>{h.source_filename} vs {h.target_filenames}</td>
                  <td>{Math.round(h.top_score)}%</td>
                  <td>
                    <div className="row-actions">
                      <button className="btn2" onClick={() => onOpen(h.id)}>Open</button>
                      <button className="btn2" onClick={() => handleDelete(h.id)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length === 0 && (
            <div className="empty">{history.length === 0 ? "No comparisons yet." : "No matches for your search."}</div>
          )}
        </div>
      </div>
    </section>
  );
}