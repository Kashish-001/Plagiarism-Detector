import codecs
import hashlib
import os
import sqlite3
import uuid

from pypdf import PdfReader

import config
import database
from nlp.preprocessing import clean_text, split_sentences


class UploadError(Exception):
    """Upload mein koi galti. app.py ise JSON error mein badal dega."""

    def __init__(self, code, message, status=400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


# ---------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------
def get_extension(filename):
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def sha256_of(data):
    return hashlib.sha256(data).hexdigest()


def _remove_file(path):
    try:
        os.remove(path)
    except OSError:
        pass


# ---------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------
def extract_pdf_text(path):
    """PDF se text nikalta hai (pypdf library). Sirf text-based PDF chalti hai."""
    try:
        reader = PdfReader(path)
        if reader.is_encrypted and not reader.decrypt(""):
            raise UploadError("PDF_ENCRYPTED", "This PDF is password protected.")
        pages = [(page.extract_text() or "") for page in reader.pages]
    except UploadError:
        raise
    except Exception:
        raise UploadError("PDF_UNREADABLE", "Could not read this PDF. The file may be corrupted.")
    return "\n\n".join(pages)


def extract_txt_text(data):
    """TXT bytes ko text mein badalta hai. Alag-alag encodings try karta hai."""
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode("utf-16")

    # Beech mein null bytes ka matlab file text nahi, binary hai
    if b"\x00" in data[:2048]:
        raise UploadError("NOT_TEXT", "This file does not look like a text file.")

    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")   # ye kabhi fail nahi hota


# ---------------------------------------------------------------
# Main: upload ka poora flow
# ---------------------------------------------------------------
def save_upload(file):
    """`file` mein .filename aur .read() hona chahiye (Flask ka FileStorage).
    Success par document ki info (bina text ke) return karta hai."""
    filename = (file.filename or "").strip()
    if not filename:
        raise UploadError("NO_FILE", "No file was selected.")

    # 1. Extension
    ext = get_extension(filename)
    if ext not in config.ALLOWED_EXTENSIONS:
        raise UploadError("BAD_TYPE", f"{filename}: only PDF or TXT files are allowed.")

    # 2. Size (MAX+1 tak hi padhte hain, taaki bahut badi file memory na bhare)
    data = file.read(config.MAX_FILE_SIZE + 1)
    if len(data) == 0:
        raise UploadError("EMPTY_FILE", f"{filename}: the file is empty.")
    if len(data) > config.MAX_FILE_SIZE:
        raise UploadError("TOO_LARGE", f"{filename}: file is larger than 5 MB.", 413)

    # 3. Content check
    if ext == "pdf" and not data.startswith(b"%PDF"):
        raise UploadError("BAD_CONTENT", f"{filename}: this is not a valid PDF file.")

    # 4. Duplicate
    digest = sha256_of(data)
    existing = database.find_document_by_hash(digest)
    if existing:
        raise UploadError(
            "DUPLICATE",
            f"{filename}: this file is already uploaded as \"{existing['filename']}\".",
            409,
        )

    # 5. Disk par save (random naam)
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(config.UPLOAD_FOLDER, stored_name)
    with open(path, "wb") as f:
        f.write(data)

    # 6 + 7. Text nikalo, saaf karo, check karo, database mein daalo
    try:
        raw = extract_pdf_text(path) if ext == "pdf" else extract_txt_text(data)
        text = clean_text(raw)                      # nlp/preprocessing.py ka cleaner

        if len(text) < config.MIN_TEXT_CHARS:
            raise UploadError(
                "NO_TEXT",
                f"{filename}: no readable text found. Scanned or image-only PDFs are not supported.",
                422,
            )

        doc_id = database.add_document(
            filename=filename,
            stored_name=stored_name,
            file_type=ext,
            file_size=len(data),
            sha256=digest,
            extracted_text=text,
            word_count=len(text.split()),
            sentence_count=len(split_sentences(text)),   # nlp/preprocessing.py ka splitter
        )
    except sqlite3.IntegrityError:
        # Do upload ek saath aaye aur dono hash check se nikal gaye
        _remove_file(path)
        raise UploadError("DUPLICATE", f"{filename}: this file is already uploaded.", 409)
    except Exception:
        _remove_file(path)   # kuch bhi bigde to adhuri file disk par na rahe
        raise

    return database.get_document(doc_id, with_text=False)


def delete_upload(doc_id):
    """Document delete karta hai (history mein use hua ho to database error dega)
    aur disk se file bhi hata deta hai. True agar delete hua, False agar nahi mila."""
    stored_name = database.delete_document(doc_id)
    if stored_name is None:
        return False
    _remove_file(os.path.join(config.UPLOAD_FOLDER, stored_name))
    return True