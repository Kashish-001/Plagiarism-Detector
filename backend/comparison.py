"""Phase 8a: poora comparison chalana (database + NLP ko jodta hai)."""
import config
import database
from nlp.matcher import compare_texts, get_terms, merge_settings

MODES = ("pair", "one_vs_many")
_RATIO_KEYS = ("near_copy_cosine", "near_copy_ngram", "similar_cosine",
               "weight_cosine", "weight_coverage")
_FLAG_KEYS = ("remove_stopwords", "use_lemmatization", "use_stemming")


class ComparisonError(Exception):
    """Comparison ki request mein galti. app.py ise JSON error mein badal dega."""

    def __init__(self, code, message, status=400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


# ---------------------------------------------------------------
# Validation
# ---------------------------------------------------------------
def clean_settings(raw):
    """UI se aayi settings jaanchta hai aur defaults ke saath milata hai."""
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ComparisonError("BAD_SETTINGS", "Settings must be an object.")
    for key in raw:
        if key not in config.DEFAULT_SETTINGS:
            raise ComparisonError("BAD_SETTINGS", f"Unknown setting: {key}.")

    settings = merge_settings(raw)
    for key in _RATIO_KEYS:
        value = settings[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise ComparisonError("BAD_SETTINGS", f"'{key}' must be a number between 0 and 1.")
        settings[key] = float(value)
    for key in _FLAG_KEYS:
        if not isinstance(settings[key], bool):
            raise ComparisonError("BAD_SETTINGS", f"'{key}' must be true or false.")
    if settings["similar_cosine"] > settings["near_copy_cosine"]:
        raise ComparisonError("BAD_SETTINGS", "'similar_cosine' cannot be higher than 'near_copy_cosine'.")
    if settings["weight_cosine"] + settings["weight_coverage"] <= 0:
        raise ComparisonError("BAD_SETTINGS", "At least one weight must be above 0.")
    return settings


def _to_id(value, name):
    if isinstance(value, bool):
        raise ComparisonError("BAD_REQUEST", f"'{name}' must be a document id.")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ComparisonError("BAD_REQUEST", f"'{name}' must be a document id.")


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
def run_comparison(mode, source_id, target_ids, settings=None):
    """Comparison chalata hai, database mein save karta hai, poora result return karta hai."""
    if mode not in MODES:
        raise ComparisonError("BAD_MODE", "Mode must be 'pair' or 'one_vs_many'.")
    settings = clean_settings(settings)
    source_id = _to_id(source_id, "source_id")

    if not isinstance(target_ids, list):
        raise ComparisonError("BAD_REQUEST", "'target_ids' must be a list of document ids.")
    ids = [_to_id(t, "target_ids") for t in target_ids]

    if mode == "pair":
        if len(ids) != 1:
            raise ComparisonError("BAD_REQUEST", "Pair mode needs exactly one second document.")
        if ids[0] == source_id:
            raise ComparisonError("SAME_DOCUMENT", "Document A and B must be different.")
        targets = ids
    else:
        targets = []
        for t in ids:                                   # source ko aur duplicates ko hatao
            if t != source_id and t not in targets:
                targets.append(t)
        if not targets:
            raise ComparisonError("BAD_REQUEST", "Upload at least one more document to compare against.")

    source = database.get_document(source_id)
    if source is None:
        raise ComparisonError("NOT_FOUND", "Document A was not found.", 404)
    target_docs = []
    for tid in targets:
        doc = database.get_document(tid)
        if doc is None:
            raise ComparisonError("NOT_FOUND", f"Document with id {tid} was not found.", 404)
        target_docs.append(doc)

    # Library = baaki saare documents; IDF behtar karne ke liye corpus mein jodte hain
    library_ids = [d["id"] for d in database.list_documents() if d["id"] != source_id]
    terms_cache = {}

    def terms_for(doc_id):
        if doc_id not in terms_cache:
            text = database.get_document(doc_id)["extracted_text"]
            terms_cache[doc_id] = get_terms(text, settings)
        return terms_cache[doc_id]

    results = []
    for target in target_docs:
        library_terms = [terms_for(i) for i in library_ids if i != target["id"]]
        result = compare_texts(source["extracted_text"], target["extracted_text"],
                               settings, library_terms)
        result["target_doc_id"] = target["id"]
        results.append(result)

    comparison_id = database.save_comparison(mode, source_id, settings, results)
    return get_full_comparison(comparison_id)


def get_full_comparison(comparison_id):
    """Comparison + dono documents ka text (frontend ko highlighting ke liye chahiye)."""
    comparison = database.get_comparison(comparison_id)
    if comparison is None:
        return None
    comparison["source_text"] = database.get_document(comparison["source_doc_id"])["extracted_text"]
    for res in comparison["results"]:
        res["target_text"] = database.get_document(res["target_doc_id"])["extracted_text"]
    return comparison