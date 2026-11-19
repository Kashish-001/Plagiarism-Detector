// "2026-11-17 16:20:00" -> "17 Nov, 16:20"
export function formatDate(value) {
  if (!value) return "";
  const d = new Date(value.replace(" ", "T"));
  if (isNaN(d)) return value;
  return d.toLocaleString("en-GB", {
    day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
  });
}

// Text + ranges [{start, end, label, index}] -> segments [{text, range|null}]
export function buildSegments(text, ranges) {
  const sorted = [...ranges].sort((a, b) => a.start - b.start);
  const segments = [];
  let cursor = 0;

  for (const r of sorted) {
    if (r.start < cursor || r.end > text.length) continue; // overlap ya galat range skip
    if (r.start > cursor) segments.push({ text: text.slice(cursor, r.start), range: null });
    segments.push({ text: text.slice(r.start, r.end), range: r });
    cursor = r.end;
  }
  if (cursor < text.length) segments.push({ text: text.slice(cursor), range: null });
  return segments;
}

export const verdictClass = (verdict) =>
  "v-" + verdict.toLowerCase().replace(/\s+/g, "");

export const labelClass = (label) => (label === "Near-copy" ? "c-near" : "c-sim");