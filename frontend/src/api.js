// true  -> sample data (backend ki zarurat nahi)
// false -> asli Flask backend
const USE_MOCK = false;
const BASE = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

/* ====================== REAL (Flask) ====================== */
async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, options);
  } catch {
    throw new Error("Cannot reach the server. Is the backend running?");
  }
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      message = body.error?.message || message;
    } catch { /* body JSON nahi tha */ }
    throw new Error(message);
  }
  return res.status === 204 ? null : res.json();
}

const real = {
  listDocuments: () => request("/documents"),
  uploadDocument: (file) => {
    const form = new FormData();
    form.append("files", file);
    return request("/documents", { method: "POST", body: form });
  },
  deleteDocument: (id) => request(`/documents/${id}`, { method: "DELETE" }),
  runComparison: (payload) =>
    request("/comparisons", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  listComparisons: () => request("/comparisons"),
  getComparison: (id) => request(`/comparisons/${id}`),
  deleteComparison: (id) => request(`/comparisons/${id}`, { method: "DELETE" }),
  downloadReport: (id) => window.open(`${BASE}/comparisons/${id}/report`, "_blank"),
};

/* ====================== MOCK (sample data) ====================== */
const delay = (ms) => new Promise((r) => setTimeout(r, ms));
const now = () => new Date().toISOString().slice(0, 19).replace("T", " ");

const TEXT_A =
  "Climate change is one of the most pressing issues of our time. " +
  "Rising global temperatures are causing sea levels to rise and weather patterns to shift. " +
  "Many governments have set targets to cut emissions. " +
  "Renewable energy now supplies a growing share of electricity. " +
  "Further research is needed on storage.";

const TEXT_B =
  "The report begins with a short history of energy policy. " +
  "Rising global temperatures are causing sea levels to rise and weather patterns to shift. " +
  "Targets differ widely between countries. " +
  "A growing share of electricity is now supplied by renewable sources.";

const PAIRS = [
  [
    "Rising global temperatures are causing sea levels to rise and weather patterns to shift.",
    "Rising global temperatures are causing sea levels to rise and weather patterns to shift.",
    0.98, 1.0, "Near-copy",
  ],
  [
    "Renewable energy now supplies a growing share of electricity.",
    "A growing share of electricity is now supplied by renewable sources.",
    0.74, 0.18, "Similar",
  ],
];

function mockMatches() {
  return PAIRS.map(([a, b, cosine, ngram, label]) => {
    const a_start = TEXT_A.indexOf(a);
    const b_start = TEXT_B.indexOf(b);
    return {
      sent_a_text: a, sent_b_text: b,
      a_start, a_end: a_start + a.length,
      b_start, b_end: b_start + b.length,
      cosine, ngram_overlap: ngram, label,
    };
  });
}

function verdictFor(score) {
  if (score < 25) return "Low";
  if (score < 50) return "Moderate";
  if (score < 75) return "High";
  return "Very High";
}

let docs = [
  { id: 1, filename: "essay_final.pdf", file_type: "pdf", file_size: 220000, word_count: 1842, uploaded_at: "2026-11-17 16:20:00" },
  { id: 2, filename: "reference_paper.txt", file_type: "txt", file_size: 14000, word_count: 2310, uploaded_at: "2026-11-17 16:22:00" },
  { id: 3, filename: "notes_week3.pdf", file_type: "pdf", file_size: 98000, word_count: 960, uploaded_at: "2026-11-16 11:05:00" },
];
let nextDocId = 4;
let nextCompId = 1;
let history = [];
const store = {};

function createMockComparison({ mode, source_id, target_ids, settings }) {
  const source = docs.find((d) => d.id === source_id);
  const results = target_ids.map((tid, i) => {
    const target = docs.find((d) => d.id === tid);
    const overall = 60.5 - i * 12;
    return {
      target_doc_id: tid,
      target_filename: target.filename,
      target_text: TEXT_B,
      doc_cosine: 0.71 - i * 0.05,
      bigram_jaccard: 0.34,
      trigram_containment: 0.58,
      coverage_a_in_b: 40,
      coverage_b_in_a: 50,
      overall_score: overall,
      verdict: verdictFor(overall),
      matches: mockMatches(),
    };
  });
  const comp = {
    id: nextCompId++, mode,
    source_doc_id: source_id, source_filename: source.filename, source_text: TEXT_A,
    created_at: now(), settings, results,
  };
  store[comp.id] = comp;
  history.unshift({
    id: comp.id, mode, created_at: comp.created_at,
    source_filename: source.filename,
    target_count: results.length,
    top_score: Math.max(...results.map((r) => r.overall_score)),
    target_filenames: results.map((r) => r.target_filename).join(", "),
  });
  return comp;
}

// Pehle se ek comparison history mein rakha hai, taaki UI khaali na dikhe
createMockComparison({ mode: "pair", source_id: 1, target_ids: [2], settings: {} });

const mock = {
  listDocuments: async () => { await delay(150); return [...docs]; },
  uploadDocument: async (file) => {
    await delay(400);
    docs.unshift({
      id: nextDocId++, filename: file.name,
      file_type: file.name.split(".").pop().toLowerCase(),
      file_size: file.size, word_count: Math.max(1, Math.round(file.size / 6)),
      uploaded_at: now(),
    });
  },
  deleteDocument: async (id) => {
    await delay(150);
    const used = Object.values(store).filter(
      (c) => c.source_doc_id === id || c.results.some((r) => r.target_doc_id === id)
    ).length;
    if (used > 0) throw new Error(`This document is used in ${used} comparison(s). Delete those first.`);
    docs = docs.filter((d) => d.id !== id);
  },
  runComparison: async (payload) => { await delay(900); return createMockComparison(payload); },
  listComparisons: async () => { await delay(100); return [...history]; },
  getComparison: async (id) => { await delay(200); return store[id]; },
  deleteComparison: async (id) => {
    await delay(150);
    delete store[id];
    history = history.filter((h) => h.id !== id);
  },
  downloadReport: () => alert("PDF report backend ban jaane ke baad milega."),
};

export default USE_MOCK ? mock : real;