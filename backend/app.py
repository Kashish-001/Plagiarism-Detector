"""Phase 8b: Flask server. Sirf HTTP ka kaam: request lo, jaanch karo, function bulao, JSON do."""
import io
import logging

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

import comparison
import config
import database
import extraction
import report
from comparison import ComparisonError
from extraction import UploadError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_FILE_SIZE * 4     # ek request mein kuch files chalengi
CORS(app, origins=[config.FRONTEND_ORIGIN, "http://127.0.0.1:5173"])
database.init_db()


def error_response(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status


def not_found(what):
    return error_response("NOT_FOUND", f"{what} not found.", 404)


# ---------------------------------------------------------------
# Error handlers: har galti {"error": {"code", "message"}} shape mein
# ---------------------------------------------------------------
@app.errorhandler(UploadError)
@app.errorhandler(ComparisonError)
def handle_app_error(err):
    return error_response(err.code, err.message, err.status)


@app.errorhandler(database.DocumentInUseError)
def handle_in_use(err):
    return error_response("DOCUMENT_IN_USE", str(err), 409)


@app.errorhandler(HTTPException)
def handle_http_error(err):
    if err.code == 413:
        return error_response("TOO_LARGE", "The upload is too large (limit is 5 MB per file).", 413)
    return error_response(err.name.upper().replace(" ", "_"), err.description, err.code)


@app.errorhandler(Exception)
def handle_unexpected(err):
    logging.exception("Unexpected error")
    return error_response("SERVER_ERROR", "Something went wrong on the server.", 500)


# ---------------------------------------------------------------
# System
# ---------------------------------------------------------------
@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/settings/defaults")
def default_settings():
    return jsonify(config.DEFAULT_SETTINGS)


# ---------------------------------------------------------------
# Documents
# ---------------------------------------------------------------
@app.post("/api/documents")
def upload_documents():
    files = request.files.getlist("files")
    if not files:
        raise UploadError("NO_FILE", "No file was selected.")

    uploaded, failures = [], []
    for f in files:
        try:
            uploaded.append(extraction.save_upload(f))
        except UploadError as err:
            failures.append(err)

    if not uploaded:
        raise failures[0]                       # sab fail hui: pehli galti dikhao
    return jsonify({
        "uploaded": uploaded,
        "errors": [{"code": e.code, "message": e.message} for e in failures],
    }), 201


@app.get("/api/documents")
def list_documents():
    return jsonify(database.list_documents())


@app.get("/api/documents/<int:doc_id>")
def get_document(doc_id):
    doc = database.get_document(doc_id)
    return jsonify(doc) if doc else not_found("Document")


@app.delete("/api/documents/<int:doc_id>")
def delete_document(doc_id):
    if not extraction.delete_upload(doc_id):
        return not_found("Document")
    return "", 204


# ---------------------------------------------------------------
# Comparisons
# ---------------------------------------------------------------
@app.post("/api/comparisons")
def create_comparison():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ComparisonError("BAD_REQUEST", "Request body must be JSON.")
    result = comparison.run_comparison(
        data.get("mode"), data.get("source_id"), data.get("target_ids"), data.get("settings"))
    return jsonify(result), 201


@app.get("/api/comparisons")
def list_comparisons():
    search = (request.args.get("search") or "").strip() or None
    return jsonify(database.list_comparisons(search))


@app.get("/api/comparisons/<int:comparison_id>")
def get_comparison(comparison_id):
    result = comparison.get_full_comparison(comparison_id)
    return jsonify(result) if result else not_found("Comparison")


@app.delete("/api/comparisons/<int:comparison_id>")
def delete_comparison(comparison_id):
    if not database.delete_comparison(comparison_id):
        return not_found("Comparison")
    return "", 204


@app.get("/api/comparisons/<int:comparison_id>/report")
def download_report(comparison_id):
    result = comparison.get_full_comparison(comparison_id)
    if result is None:
        return not_found("Comparison")
    pdf = report.build_pdf_report(result)
    return send_file(io.BytesIO(pdf), mimetype="application/pdf", as_attachment=True,
                     download_name=f"similarity-report-{comparison_id}.pdf")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)