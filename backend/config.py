import os

# ---------- Paths ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
INSTANCE_FOLDER = os.path.join(BASE_DIR, "instance")
DATABASE_PATH = os.path.join(INSTANCE_FOLDER, "plagiarism.db")
STOPWORDS_PATH = os.path.join(BASE_DIR, "nlp", "stopwords_en.txt")

# ---------- Upload limits ----------
ALLOWED_EXTENSIONS = {"pdf", "txt"}
MAX_FILE_SIZE = 5 * 1024 * 1024      # 5 MB
MIN_TEXT_CHARS = 50                  # kam text => scanned/empty PDF maana jayega

# ---------- Web ----------
FRONTEND_ORIGIN = "http://localhost:5173"   # Vite ka default port

# ---------- Comparison defaults (UI se badle ja sakte hain) ----------
DEFAULT_SETTINGS = {
    # Sentence labels
    "near_copy_cosine": 0.85,     # cosine >= 0.85  -> Exact/Near-copy
    "near_copy_ngram": 0.70,      # trigram overlap >= 0.70 -> Exact/Near-copy
    "similar_cosine": 0.60,       # cosine >= 0.60  -> Similar

    # Overall score = w1 * doc_cosine + w2 * coverage
    "weight_cosine": 0.5,
    "weight_coverage": 0.5,

    # Preprocessing options
    "remove_stopwords": True,
    "use_lemmatization": True,
    "use_stemming": True,
}

# ---------- Verdict bands: (upper limit %, label) ----------
VERDICT_BANDS = [
    (25, "Low"),
    (50, "Moderate"),
    (75, "High"),
    (100, "Very High"),
]

# ---------- Runtime folders ----------
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(INSTANCE_FOLDER, exist_ok=True)