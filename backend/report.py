"""Phase 10: PDF report (ReportLab library). Comparison ka poora result ek PDF mein."""
import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

MAX_MATCHES_PER_TARGET = 200     # bahut bade result se PDF bhaari na ho
MAX_CELL_CHARS = 400             # ek lamba sentence poore page se bada na ho jaye

INK = colors.HexColor("#26332E")
MUTED = colors.HexColor("#5B6B64")
ACCENT = colors.HexColor("#2F7D6D")
HEADER_BG = colors.HexColor("#E3EFEA")
LINE = colors.HexColor("#C9D5CF")
AMBER = colors.HexColor("#FBDDB8")
BLUE = colors.HexColor("#CFE6F6")

SETTING_LABELS = [
    ("near_copy_cosine", "Near-copy cosine threshold"),
    ("near_copy_ngram", "Near-copy trigram overlap threshold"),
    ("similar_cosine", "Similar cosine threshold"),
    ("weight_cosine", "Score weight: document cosine"),
    ("weight_coverage", "Score weight: sentence coverage"),
    ("remove_stopwords", "Stopword removal"),
    ("use_lemmatization", "Lemmatization"),
    ("use_stemming", "Stemming"),
]

_styles = getSampleStyleSheet()
TITLE = ParagraphStyle("T", parent=_styles["Title"], fontName="Helvetica-Bold", fontSize=20,
                       textColor=ACCENT, alignment=0, spaceAfter=4)
H2 = ParagraphStyle("H2", parent=_styles["Heading2"], fontName="Helvetica-Bold", fontSize=13,
                    textColor=INK, spaceBefore=14, spaceAfter=6)
BODY = ParagraphStyle("B", parent=_styles["BodyText"], fontName="Helvetica", fontSize=10,
                      textColor=INK, leading=14)
SMALL = ParagraphStyle("S", parent=BODY, fontSize=9, textColor=MUTED)
CELL = ParagraphStyle("C", parent=BODY, fontSize=8, leading=10)
CELL_HEAD = ParagraphStyle("CH", parent=CELL, fontName="Helvetica-Bold")


def _safe(value, limit=None):
    """Helvetica sirf Latin-1 akshar dikha sakta hai; baaki '?' ban jate hain. XML escape bhi."""
    text = str(value)
    if limit and len(text) > limit:
        text = text[:limit].rstrip() + "..."
    return escape(text.encode("cp1252", "replace").decode("cp1252"))


def _p(value, style=CELL, limit=None):
    return Paragraph(_safe(value, limit), style)


def _grid(extra=None):
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    return TableStyle(commands + (extra or []))


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 10 * mm, "Plagiarism and Text Similarity Detection System")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _summary_table(results):
    rows = [[_p(h, CELL_HEAD) for h in
             ("Document B", "Score", "Verdict", "Cosine", "Jaccard (2-gram)",
              "Containment (3-gram)", "Coverage A in B", "Coverage B in A")]]
    for r in results:
        rows.append([
            _p(r["target_filename"]), _p(f"{r['overall_score']:.1f}%"), _p(r["verdict"]),
            _p(f"{r['doc_cosine']:.2f}"), _p(f"{r['bigram_jaccard']:.2f}"),
            _p(f"{r['trigram_containment']:.2f}"),
            _p(f"{r['coverage_a_in_b']:.0f}%"), _p(f"{r['coverage_b_in_a']:.0f}%"),
        ])
    widths = [44, 15, 19, 15, 20, 22, 20, 19]
    table = Table(rows, colWidths=[w * mm for w in widths], repeatRows=1)
    table.setStyle(_grid())
    return table


def _settings_table(settings):
    rows = [[_p("Setting", CELL_HEAD), _p("Value", CELL_HEAD)]]
    for key, label in SETTING_LABELS:
        if key not in settings:
            continue
        value = settings[key]
        if isinstance(value, bool):
            value = "Yes" if value else "No"
        rows.append([_p(label), _p(value)])
    table = Table(rows, colWidths=[80 * mm, 40 * mm], hAlign="LEFT")
    table.setStyle(_grid())
    return table


def _matches_table(matches):
    shown = matches[:MAX_MATCHES_PER_TARGET]
    rows = [[_p(h, CELL_HEAD) for h in ("#", "Sentence in A", "Sentence in B", "Cosine", "N-gram", "Label")]]
    shading = []
    for i, m in enumerate(shown, start=1):
        rows.append([
            _p(i), _p(m["sent_a_text"], limit=MAX_CELL_CHARS), _p(m["sent_b_text"], limit=MAX_CELL_CHARS),
            _p(f"{m['cosine']:.2f}"), _p(f"{m['ngram_overlap']:.2f}"), _p(m["label"]),
        ])
        shading.append(("BACKGROUND", (5, i), (5, i), AMBER if m["label"] == "Near-copy" else BLUE))
    widths = [8, 56, 56, 15, 15, 24]
    table = Table(rows, colWidths=[w * mm for w in widths], repeatRows=1)
    table.setStyle(_grid(shading))
    return table


def build_pdf_report(comparison):
    """comparison = comparison.get_full_comparison() ka result. Return: PDF ke bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"Similarity Report #{comparison['id']}",
    )
    mode = "Pair" if comparison["mode"] == "pair" else "One vs Many"
    results = comparison["results"]

    story = [
        Paragraph("Similarity Report", TITLE),
        _p(f"Report #{comparison['id']}  |  {comparison['created_at']}  |  Mode: {mode}", SMALL, None),
        Spacer(1, 6),
        _p(f"Document A (source): {comparison['source_filename']}", BODY),
        Spacer(1, 4),
        Paragraph("Summary", H2),
        _summary_table(results),
        Spacer(1, 4),
        _p("Score = weighted mix of document cosine similarity and sentence coverage. "
           "Cosine and n-gram values range from 0 to 1.", SMALL),
        Paragraph("Settings used", H2),
        _settings_table(comparison["settings"]),
    ]

    for r in results:
        story.append(Paragraph(_safe(f"A vs {r['target_filename']}"), H2))
        story.append(_p(f"Overall score {r['overall_score']:.1f}% ({r['verdict']}). "
                        f"{len(r['matches'])} matching sentence pair(s).", BODY))
        story.append(Spacer(1, 6))
        if not r["matches"]:
            story.append(_p("No similar sentences were found with the current thresholds.", SMALL))
            continue
        story.append(_matches_table(r["matches"]))
        if len(r["matches"]) > MAX_MATCHES_PER_TARGET:
            story.append(Spacer(1, 4))
            story.append(_p(f"Showing the first {MAX_MATCHES_PER_TARGET} of {len(r['matches'])} matches.", SMALL))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()