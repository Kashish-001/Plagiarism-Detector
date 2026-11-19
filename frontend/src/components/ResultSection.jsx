import { useState } from "react";
import api from "../api";
import { buildSegments, labelClass, verdictClass } from "../utils";

function ScoreRing({ score, verdict }) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const filled = (Math.min(Math.max(score, 0), 100) / 100) * circumference;
  return (
    <div className="ring">
      <svg width="128" height="128" viewBox="0 0 128 128" role="img"
           aria-label={`Overall similarity ${Math.round(score)} percent`}>
        <circle cx="64" cy="64" r={radius} fill="none" stroke="#E3EAE6" strokeWidth="12" />
        <circle cx="64" cy="64" r={radius} fill="none" stroke="#2F7D6D" strokeWidth="12"
                strokeLinecap="round" strokeDasharray={`${filled} ${circumference}`}
                transform="rotate(-90 64 64)" />
      </svg>
      <div className="ring-text">
        <b>{Math.round(score)}%</b>
        <span className={`chip ${verdictClass(verdict)}`}>{verdict}</span>
      </div>
    </div>
  );
}

function Metric({ value, label }) {
  return (
    <div className="metric"><b>{value}</b><span>{label}</span></div>
  );
}

// side = "a" ya "b": kis document ke offsets use karne hain
function HighlightedText({ text, matches, side, activeIndex }) {
  const startKey = side === "a" ? "a_start" : "b_start";
  const endKey = side === "a" ? "a_end" : "b_end";
  const ranges = matches.map((m, i) => ({
    start: m[startKey], end: m[endKey], label: m.label, index: i,
  }));
  const segments = buildSegments(text, ranges);

  return (
    <div className="doc">
      {segments.map((seg, i) =>
        seg.range ? (
          <mark
            key={i}
            id={`${side}-${seg.range.index}`}
            className={`${seg.range.label === "Near-copy" ? "hl-near" : "hl-sim"} ${
              seg.range.index === activeIndex ? "hl-active" : ""
            }`}
          >
            {seg.text}
          </mark>
        ) : (
          <span key={i}>{seg.text}</span>
        )
      )}
    </div>
  );
}

// Sirf document ke andar scroll karta hai, poora page nahi
function scrollInside(id) {
  const el = document.getElementById(id);
  const box = el?.parentElement;
  if (box) box.scrollTo({ top: el.offsetTop - box.clientHeight / 2, behavior: "smooth" });
}

export default function ResultSection({ result }) {
  const [targetIdx, setTargetIdx] = useState(0);
  const [active, setActive] = useState(null);
  const r = result.results[targetIdx];

  function showMatch(i) {
    setActive(i);
    scrollInside(`a-${i}`);
    scrollInside(`b-${i}`);
  }

  return (
    <section className="sec" id="result">
      <div className="card">
        <div className="head-row">
          <div>
            <h2>Result</h2>
            <p className="sub" style={{ margin: 0 }}>
              {result.source_filename} vs {r.target_filename}
            </p>
          </div>
          <button className="btn" onClick={() => api.downloadReport(result.id)}>
            Download PDF report
          </button>
        </div>

        {result.results.length > 1 && (
          <div style={{ maxWidth: 360, marginBottom: 20 }}>
            <label htmlFor="target">Compared document</label>
            <select id="target" value={targetIdx}
                    onChange={(e) => { setTargetIdx(Number(e.target.value)); setActive(null); }}>
              {result.results.map((x, i) => (
                <option key={x.target_doc_id} value={i}>
                  {x.target_filename} ({Math.round(x.overall_score)}%)
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="score-row">
          <ScoreRing score={r.overall_score} verdict={r.verdict} />
          <div className="metrics">
            <Metric value={r.doc_cosine.toFixed(2)} label="Document cosine" />
            <Metric value={r.bigram_jaccard.toFixed(2)} label="Bigram Jaccard" />
            <Metric value={r.trigram_containment.toFixed(2)} label="Trigram containment" />
            <Metric value={`${Math.round(r.coverage_a_in_b)}%`} label="Coverage A in B" />
            <Metric value={`${Math.round(r.coverage_b_in_a)}%`} label="Coverage B in A" />
          </div>
        </div>

        <div className="legend">
          <span className="chip c-near">Near-copy</span>
          <span className="chip c-sim">Similar</span>
        </div>

        <div className="panels">
          <div>
            <label>Document A: {result.source_filename}</label>
            <HighlightedText text={result.source_text} matches={r.matches} side="a" activeIndex={active} />
          </div>
          <div>
            <label>Document B: {r.target_filename}</label>
            <HighlightedText text={r.target_text} matches={r.matches} side="b" activeIndex={active} />
          </div>
        </div>

        <div style={{ marginTop: 24 }}>
          <label>Matched sentences ({r.matches.length})</label>
          {r.matches.length === 0 ? (
            <div className="empty">No similar sentences found with the current thresholds.</div>
          ) : (
            <div className="tw">
              <table>
                <thead>
                  <tr>
                    <th>#</th><th>Sentence in A</th><th>Sentence in B</th>
                    <th>Cosine</th><th>Label</th><th></th>
                  </tr>
                </thead>
                <tbody>
                  {r.matches.map((m, i) => (
                    <tr key={i}>
                      <td>{i + 1}</td>
                      <td className="cell-text">{m.sent_a_text}</td>
                      <td className="cell-text">{m.sent_b_text}</td>
                      <td>{m.cosine.toFixed(2)}</td>
                      <td><span className={`chip ${labelClass(m.label)}`}>{m.label}</span></td>
                      <td><button className="btn2" onClick={() => showMatch(i)}>View</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}