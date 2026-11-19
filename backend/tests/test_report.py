import io

import pytest
from pypdf import PdfReader

import config
import database
from app import app
from report import build_pdf_report

TEXT_A = (
    "Climate change is one of the most pressing issues of our time. "
    "Rising global temperatures are causing sea levels to rise and weather patterns to shift. "
    "Many governments have set targets to cut emissions. "
    "Renewable energy now supplies a growing share of electricity. "
    "Further research is needed on storage."
)
TEXT_B = (
    "The report begins with a short history of energy policy. "
    "Rising global temperatures are causing sea levels to rise and weather patterns to shift. "
    "Targets differ widely between countries. "
    "A growing share of electricity is now supplied by renewable sources."
)


def make_comparison(matches, filename="b.txt"):
    return {
        "id": 7, "mode": "pair", "created_at": "2026-11-19 10:00:00",
        "source_filename": "a.txt",
        "settings": {"near_copy_cosine": 0.85, "similar_cosine": 0.6, "use_stemming": True},
        "results": [{
            "target_filename": filename, "overall_score": 47.9, "verdict": "Moderate",
            "doc_cosine": 0.4587, "bigram_jaccard": 0.2429, "trigram_containment": 0.3191,
            "coverage_a_in_b": 40.0, "coverage_b_in_a": 50.0, "matches": matches,
        }],
    }


def match(a="Rising global temperatures are causing sea levels to rise.", label="Near-copy"):
    return {"sent_a_text": a, "sent_b_text": a, "cosine": 1.0, "ngram_overlap": 1.0, "label": label}


def pdf_text(pdf_bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() for page in reader.pages)


def test_report_is_a_valid_pdf():
    pdf = build_pdf_report(make_comparison([match(), match(label="Similar")]))
    assert pdf.startswith(b"%PDF")
    text = pdf_text(pdf)
    assert "Similarity Report" in text
    assert "b.txt" in text
    assert "Moderate" in text
    assert "Near-copy" in text and "Similar" in text


def test_report_without_matches():
    text = pdf_text(build_pdf_report(make_comparison([])))
    assert "No similar sentences" in text


def test_report_survives_special_characters():
    tricky = match(a="<b>Bold</b> & \u201cquotes\u201d \u0928\u092e\u0938\u094d\u0924\u0947 sentence here.")
    pdf = build_pdf_report(make_comparison([tricky], filename="we<ird>&name.txt"))
    assert pdf.startswith(b"%PDF")


def test_report_handles_very_long_sentence_and_many_matches():
    long_sentence = "word " * 5000
    matches = [match(a=long_sentence)] + [match() for _ in range(250)]
    text = pdf_text(build_pdf_report(make_comparison(matches)))
    assert "Showing the first 200 of 251 matches" in text


@pytest.fixture
def client(tmp_path, monkeypatch):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    monkeypatch.setattr(config, "DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(config, "UPLOAD_FOLDER", str(uploads))
    database.init_db()
    app.config["TESTING"] = True
    return app.test_client()


def upload(client, name, text):
    r = client.post("/api/documents", data={"files": (io.BytesIO(text.encode()), name)},
                    content_type="multipart/form-data")
    return r.get_json()["uploaded"][0]["id"]


def test_report_endpoint_returns_pdf(client):
    a, b = upload(client, "a.txt", TEXT_A), upload(client, "b.txt", TEXT_B)
    cid = client.post("/api/comparisons",
                      json={"mode": "pair", "source_id": a, "target_ids": [b]}).get_json()["id"]
    r = client.get(f"/api/comparisons/{cid}/report")
    assert r.status_code == 200
    assert r.mimetype == "application/pdf"
    assert "attachment" in r.headers["Content-Disposition"]
    assert r.data.startswith(b"%PDF")
    assert "a.txt" in pdf_text(r.data)


def test_report_for_unknown_comparison_is_404(client):
    r = client.get("/api/comparisons/999/report")
    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "NOT_FOUND"