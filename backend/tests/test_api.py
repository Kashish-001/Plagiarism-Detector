import io

import pytest

import config
import database
from app import app

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
TEXT_C = (
    "Photosynthesis converts sunlight into chemical energy inside the chloroplasts of green plants. "
    "Mitochondria produce most of the energy that animal cells need."
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Har test ke liye alag, khaali database aur uploads folder (asli data ko haath nahi lagta)."""
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    monkeypatch.setattr(config, "DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(config, "UPLOAD_FOLDER", str(uploads))
    database.init_db()
    app.config["TESTING"] = True
    return app.test_client()


def upload(client, name, text):
    return client.post(
        "/api/documents",
        data={"files": (io.BytesIO(text.encode()), name)},
        content_type="multipart/form-data",
    )


def upload_three(client):
    ids = []
    for name, text in (("a.txt", TEXT_A), ("b.txt", TEXT_B), ("c.txt", TEXT_C)):
        ids.append(upload(client, name, text).get_json()["uploaded"][0]["id"])
    return ids


def test_health(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}


def test_default_settings(client):
    data = client.get("/api/settings/defaults").get_json()
    assert data["similar_cosine"] == 0.6


def test_upload_and_list(client):
    r = upload(client, "a.txt", TEXT_A)
    assert r.status_code == 201
    docs = client.get("/api/documents").get_json()
    assert [d["filename"] for d in docs] == ["a.txt"]


def test_duplicate_upload_is_rejected(client):
    upload(client, "a.txt", TEXT_A)
    r = upload(client, "copy.txt", TEXT_A)
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "DUPLICATE"


def test_bad_file_type_is_rejected(client):
    r = upload(client, "a.docx", TEXT_A)
    assert r.status_code == 400
    assert r.get_json()["error"]["code"] == "BAD_TYPE"


def test_upload_without_file(client):
    r = client.post("/api/documents", data={}, content_type="multipart/form-data")
    assert r.status_code == 400


def test_pair_comparison(client):
    a, b, _ = upload_three(client)
    r = client.post("/api/comparisons", json={"mode": "pair", "source_id": a, "target_ids": [b]})
    assert r.status_code == 201
    data = r.get_json()
    assert data["source_text"] == TEXT_A
    result = data["results"][0]
    assert result["target_text"] == TEXT_B
    assert result["target_filename"] == "b.txt"
    assert len(result["matches"]) >= 2
    assert result["verdict"] in ("Low", "Moderate", "High", "Very High")


def test_one_vs_many_comparison(client):
    a, b, c = upload_three(client)
    r = client.post("/api/comparisons",
                    json={"mode": "one_vs_many", "source_id": a, "target_ids": [a, b, c]})
    data = r.get_json()
    assert len(data["results"]) == 2                   # source khud ko hata diya gaya
    assert data["results"][0]["overall_score"] >= data["results"][1]["overall_score"]
    assert data["results"][0]["target_filename"] == "b.txt"


def test_same_document_is_rejected(client):
    a, _, _ = upload_three(client)
    r = client.post("/api/comparisons", json={"mode": "pair", "source_id": a, "target_ids": [a]})
    assert r.status_code == 400
    assert r.get_json()["error"]["code"] == "SAME_DOCUMENT"


def test_unknown_document_gives_404(client):
    a, _, _ = upload_three(client)
    r = client.post("/api/comparisons", json={"mode": "pair", "source_id": a, "target_ids": [999]})
    assert r.status_code == 404


def test_bad_settings_are_rejected(client):
    a, b, _ = upload_three(client)
    body = {"mode": "pair", "source_id": a, "target_ids": [b], "settings": {"similar_cosine": 5}}
    assert client.post("/api/comparisons", json=body).status_code == 400
    body["settings"] = {"similar_cosine": 0.9, "near_copy_cosine": 0.5}
    assert client.post("/api/comparisons", json=body).status_code == 400


def test_body_must_be_json(client):
    r = client.post("/api/comparisons", data="not json", content_type="text/plain")
    assert r.status_code == 400


def test_history_open_and_delete(client):
    a, b, _ = upload_three(client)
    created = client.post("/api/comparisons",
                          json={"mode": "pair", "source_id": a, "target_ids": [b]}).get_json()
    cid = created["id"]

    history = client.get("/api/comparisons").get_json()
    assert history[0]["id"] == cid and history[0]["target_filenames"] == "b.txt"
    assert client.get("/api/comparisons?search=zzz").get_json() == []
    assert client.get(f"/api/comparisons/{cid}").get_json()["source_filename"] == "a.txt"

    assert client.delete(f"/api/comparisons/{cid}").status_code == 204
    assert client.get(f"/api/comparisons/{cid}").status_code == 404


def test_document_in_history_cannot_be_deleted(client):
    a, b, _ = upload_three(client)
    cid = client.post("/api/comparisons",
                      json={"mode": "pair", "source_id": a, "target_ids": [b]}).get_json()["id"]
    r = client.delete(f"/api/documents/{a}")
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "DOCUMENT_IN_USE"

    client.delete(f"/api/comparisons/{cid}")
    assert client.delete(f"/api/documents/{a}").status_code == 204


def test_unknown_url_returns_json_error(client):
    r = client.get("/api/nothing")
    assert r.status_code == 404
    assert "error" in r.get_json()