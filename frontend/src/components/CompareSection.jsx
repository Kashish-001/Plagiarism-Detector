import { useState } from "react";

const DEFAULTS = {
  near_copy_cosine: "0.85",
  similar_cosine: "0.60",
  weight_cosine: "0.5",
};

export default function CompareSection({ documents, onCompare, loading, error }) {
  const [mode, setMode] = useState("pair");
  const [docA, setDocA] = useState("");
  const [docB, setDocB] = useState("");
  const [s, setS] = useState(DEFAULTS);
  const [localError, setLocalError] = useState(null);

  const setField = (key) => (e) => setS({ ...s, [key]: e.target.value });

  function submit() {
    setLocalError(null);
    if (!docA) return setLocalError("Please select Document A.");

    let targets;
    if (mode === "pair") {
      if (!docB) return setLocalError("Please select Document B.");
      if (docA === docB) return setLocalError("Document A and B must be different.");
      targets = [Number(docB)];
    } else {
      targets = documents.filter((d) => d.id !== Number(docA)).map((d) => d.id);
      if (targets.length === 0)
        return setLocalError("Upload at least one more document to compare against.");
    }

    const near = parseFloat(s.near_copy_cosine);
    const sim = parseFloat(s.similar_cosine);
    const w = parseFloat(s.weight_cosine);
    if ([near, sim, w].some((v) => isNaN(v) || v < 0 || v > 1))
      return setLocalError("Thresholds and weight must be numbers between 0 and 1.");
    if (sim > near)
      return setLocalError("'Similar cosine' cannot be higher than 'Near-copy cosine'.");

    onCompare({
      mode,
      source_id: Number(docA),
      target_ids: targets,
      settings: {
        near_copy_cosine: near,
        similar_cosine: sim,
        weight_cosine: w,
        weight_coverage: +(1 - w).toFixed(2),
      },
    });
  }

  const shownError = localError || error;
  const others = documents.filter((d) => String(d.id) !== docA);

  return (
    <section className="sec" id="compare">
      <div className="card">
        <h2>Compare</h2>
        <p className="sub">Check two documents, or one document against the whole library.</p>

        <div className="seg" role="group" aria-label="Comparison mode">
          <button className={mode === "pair" ? "on" : ""} onClick={() => setMode("pair")}>Pair</button>
          <button className={mode === "one_vs_many" ? "on" : ""} onClick={() => setMode("one_vs_many")}>One vs Many</button>
        </div>

        <div className="grid">
          <div>
            <label htmlFor="docA">Document A</label>
            <select id="docA" value={docA} onChange={(e) => setDocA(e.target.value)}>
              <option value="">Select a document</option>
              {documents.map((d) => <option key={d.id} value={d.id}>{d.filename}</option>)}
            </select>
          </div>

          {mode === "pair" ? (
            <div>
              <label htmlFor="docB">Document B</label>
              <select id="docB" value={docB} onChange={(e) => setDocB(e.target.value)}>
                <option value="">Select a document</option>
                {others.map((d) => <option key={d.id} value={d.id}>{d.filename}</option>)}
              </select>
            </div>
          ) : (
            <div>
              <label>Compared against</label>
              <p className="muted" style={{ margin: 0, paddingTop: 10 }}>
                All other documents in your library ({others.length}).
              </p>
            </div>
          )}
        </div>

        <div className="grid" style={{ marginTop: 16 }}>
          <div>
            <label htmlFor="t1">Near-copy cosine</label>
            <input id="t1" type="number" step="0.05" min="0" max="1"
                   value={s.near_copy_cosine} onChange={setField("near_copy_cosine")} />
          </div>
          <div>
            <label htmlFor="t2">Similar cosine</label>
            <input id="t2" type="number" step="0.05" min="0" max="1"
                   value={s.similar_cosine} onChange={setField("similar_cosine")} />
          </div>
          <div>
            <label htmlFor="t3">Weight: cosine (coverage gets the rest)</label>
            <input id="t3" type="number" step="0.1" min="0" max="1"
                   value={s.weight_cosine} onChange={setField("weight_cosine")} />
          </div>
        </div>

        {shownError && <div className="error">{shownError}</div>}

        <div style={{ marginTop: 20 }}>
          <button className="btn" onClick={submit} disabled={loading}>
            {loading ? (<><span className="spinner" />Comparing...</>) : "Compare documents"}
          </button>
        </div>
      </div>
    </section>
  );
}