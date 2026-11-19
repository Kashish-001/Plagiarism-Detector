import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime

import config


class DocumentInUseError(Exception):
    """Document kisi saved comparison mein use hua hai, isliye delete nahi ho sakta."""


# ---------------------------------------------------------------
# Connection
# ---------------------------------------------------------------
@contextmanager
def get_db():
    """Connection kholta hai, kaam hone par commit karke band kar deta hai."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    filename        TEXT NOT NULL,
    stored_name     TEXT NOT NULL,
    file_type       TEXT NOT NULL,
    file_size       INTEGER NOT NULL,
    sha256          TEXT NOT NULL UNIQUE,
    extracted_text  TEXT NOT NULL,
    word_count      INTEGER NOT NULL,
    sentence_count  INTEGER NOT NULL,
    uploaded_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS comparisons (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    mode           TEXT NOT NULL CHECK (mode IN ('pair', 'one_vs_many')),
    source_doc_id  INTEGER NOT NULL REFERENCES documents(id),
    settings_json  TEXT NOT NULL,
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS comparison_results (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    comparison_id        INTEGER NOT NULL REFERENCES comparisons(id) ON DELETE CASCADE,
    target_doc_id        INTEGER NOT NULL REFERENCES documents(id),
    doc_cosine           REAL NOT NULL,
    bigram_jaccard       REAL NOT NULL,
    trigram_containment  REAL NOT NULL,
    coverage_a_in_b      REAL NOT NULL,
    coverage_b_in_a      REAL NOT NULL,
    overall_score        REAL NOT NULL,
    verdict              TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sentence_matches (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id      INTEGER NOT NULL REFERENCES comparison_results(id) ON DELETE CASCADE,
    sent_a_text    TEXT NOT NULL,
    sent_b_text    TEXT NOT NULL,
    a_start        INTEGER NOT NULL,
    a_end          INTEGER NOT NULL,
    b_start        INTEGER NOT NULL,
    b_end          INTEGER NOT NULL,
    cosine         REAL NOT NULL,
    ngram_overlap  REAL NOT NULL,
    label          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_results_comparison ON comparison_results(comparison_id);
CREATE INDEX IF NOT EXISTS idx_matches_result ON sentence_matches(result_id);
"""


def init_db():
    """Tables bana deta hai (agar pehle se hain to kuch nahi karta)."""
    with get_db() as conn:
        conn.executescript(SCHEMA)


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------
# Documents
# ---------------------------------------------------------------
def add_document(filename, stored_name, file_type, file_size, sha256,
                 extracted_text, word_count, sentence_count):
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO documents
               (filename, stored_name, file_type, file_size, sha256,
                extracted_text, word_count, sentence_count, uploaded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (filename, stored_name, file_type, file_size, sha256,
             extracted_text, word_count, sentence_count, _now()),
        )
        return cur.lastrowid


def find_document_by_hash(sha256):
    """Duplicate upload pakadne ke liye."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, filename FROM documents WHERE sha256 = ?", (sha256,)
        ).fetchone()
        return dict(row) if row else None


def list_documents():
    """Library list. Text shamil nahi karte, kyunki wo bhaari hota hai."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, filename, file_type, file_size, word_count,
                      sentence_count, uploaded_at
               FROM documents ORDER BY id DESC"""
        ).fetchall()
        return [dict(r) for r in rows]


def get_document(doc_id, with_text=True):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if row is None:
            return None
        doc = dict(row)
        if not with_text:
            doc.pop("extracted_text", None)
        return doc


def delete_document(doc_id):
    """Delete karta hai. Agar history mein use hua hai to error deta hai.
    Return: stored_name (taaki disk se file bhi hata sakein), ya None agar doc nahi mila."""
    with get_db() as conn:
        used = conn.execute(
            """SELECT COUNT(DISTINCT c.id) AS n FROM comparisons c
               LEFT JOIN comparison_results r ON r.comparison_id = c.id
               WHERE c.source_doc_id = ? OR r.target_doc_id = ?""",
            (doc_id, doc_id),
        ).fetchone()["n"]
        if used > 0:
            raise DocumentInUseError(
                f"This document is used in {used} comparison(s). Delete those first."
            )
        row = conn.execute(
            "SELECT stored_name FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
        if row is None:
            return None
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        return row["stored_name"]


# ---------------------------------------------------------------
# Comparisons
# ---------------------------------------------------------------
def save_comparison(mode, source_doc_id, settings, results):
    """Poora comparison ek transaction mein save karta hai.

    results = [
        {
          "target_doc_id": 2,
          "doc_cosine": .., "bigram_jaccard": .., "trigram_containment": ..,
          "coverage_a_in_b": .., "coverage_b_in_a": ..,
          "overall_score": .., "verdict": "..",
          "matches": [ {sent_a_text, sent_b_text, a_start, a_end,
                        b_start, b_end, cosine, ngram_overlap, label}, ... ]
        }, ...
    ]
    """
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO comparisons (mode, source_doc_id, settings_json, created_at)
               VALUES (?, ?, ?, ?)""",
            (mode, source_doc_id, json.dumps(settings), _now()),
        )
        comparison_id = cur.lastrowid

        for res in results:
            cur = conn.execute(
                """INSERT INTO comparison_results
                   (comparison_id, target_doc_id, doc_cosine, bigram_jaccard,
                    trigram_containment, coverage_a_in_b, coverage_b_in_a,
                    overall_score, verdict)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (comparison_id, res["target_doc_id"], res["doc_cosine"],
                 res["bigram_jaccard"], res["trigram_containment"],
                 res["coverage_a_in_b"], res["coverage_b_in_a"],
                 res["overall_score"], res["verdict"]),
            )
            result_id = cur.lastrowid

            conn.executemany(
                """INSERT INTO sentence_matches
                   (result_id, sent_a_text, sent_b_text, a_start, a_end,
                    b_start, b_end, cosine, ngram_overlap, label)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [(result_id, m["sent_a_text"], m["sent_b_text"], m["a_start"],
                  m["a_end"], m["b_start"], m["b_end"], m["cosine"],
                  m["ngram_overlap"], m["label"]) for m in res["matches"]],
            )
        return comparison_id


def list_comparisons(search=None):
    """History list: har comparison ka summary (filename, kitne targets, sabse high score)."""
    sql = """
        SELECT c.id, c.mode, c.created_at,
               s.filename AS source_filename,
               COUNT(r.id) AS target_count,
               MAX(r.overall_score) AS top_score,
               GROUP_CONCAT(t.filename, ', ') AS target_filenames
        FROM comparisons c
        JOIN documents s ON s.id = c.source_doc_id
        LEFT JOIN comparison_results r ON r.comparison_id = c.id
        LEFT JOIN documents t ON t.id = r.target_doc_id
    """
    params = ()
    if search:
        sql += " WHERE s.filename LIKE ? OR t.filename LIKE ?"
        like = f"%{search}%"
        params = (like, like)
    sql += " GROUP BY c.id ORDER BY c.id DESC"

    with get_db() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_comparison(comparison_id):
    """Ek comparison poora: settings, har target ka result aur uske matches."""
    with get_db() as conn:
        comp = conn.execute(
            """SELECT c.*, s.filename AS source_filename
               FROM comparisons c JOIN documents s ON s.id = c.source_doc_id
               WHERE c.id = ?""",
            (comparison_id,),
        ).fetchone()
        if comp is None:
            return None

        comparison = dict(comp)
        comparison["settings"] = json.loads(comparison.pop("settings_json"))

        result_rows = conn.execute(
            """SELECT r.*, t.filename AS target_filename
               FROM comparison_results r JOIN documents t ON t.id = r.target_doc_id
               WHERE r.comparison_id = ? ORDER BY r.overall_score DESC""",
            (comparison_id,),
        ).fetchall()

        results = []
        for row in result_rows:
            res = dict(row)
            matches = conn.execute(
                "SELECT * FROM sentence_matches WHERE result_id = ? ORDER BY a_start",
                (res["id"],),
            ).fetchall()
            res["matches"] = [dict(m) for m in matches]
            results.append(res)

        comparison["results"] = results
        return comparison


def delete_comparison(comparison_id):
    """True agar delete hua. Results aur matches CASCADE se khud hat jaate hain."""
    with get_db() as conn:
        cur = conn.execute("DELETE FROM comparisons WHERE id = ?", (comparison_id,))
        return cur.rowcount > 0