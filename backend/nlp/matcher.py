"""Phase 7: sentence matching + scoring (manual).
Do documents ko compare karke: milte-julte sentences, coverage, overall score aur verdict nikalta hai."""
import config
from nlp.preprocessing import split_sentences, tokenize, remove_stopwords
from nlp.lemmatizer import lemmatize_tokens
from nlp.stemmer import stem_tokens
from nlp.ngrams import ngram_set, jaccard, containment
from nlp.tfidf import TfidfModel
from nlp.similarity import cosine_similarity

MIN_SENTENCE_TOKENS = 4     # isse chhote sentences (headings, "Yes.") compare nahi karte


# ---------------------------------------------------------------
# 1. Settings aur text ki taiyari
# ---------------------------------------------------------------
def merge_settings(settings):
    """UI ki settings ko defaults ke upar rakhta hai (jo UI ne nahi bheji, wo default)."""
    merged = dict(config.DEFAULT_SETTINGS)
    if settings:
        merged.update(settings)
    return merged


def normalize(tokens, settings):
    """Tokens ko comparison ke layak banata hai: stopwords hatao -> lemma -> stem."""
    if settings["remove_stopwords"]:
        tokens = remove_stopwords(tokens)
    if settings["use_lemmatization"]:
        tokens = lemmatize_tokens(tokens)
    if settings["use_stemming"]:
        tokens = stem_tokens(tokens)
    return tokens


def get_terms(text, settings=None):
    """Poore document ke normalized tokens (library documents ke liye bhi yahi chalta hai)."""
    return normalize(tokenize(text), merge_settings(settings))


def prepare_document(text, settings):
    """Har sentence ke do roop banata hai:
       raw   = lowercase tokens, stopwords ke saath (n-gram overlap ke liye)
       terms = normalized tokens (TF-IDF cosine ke liye)"""
    sentences = []
    for s in split_sentences(text):
        raw = tokenize(s["text"])
        terms = normalize(raw, settings)
        sentences.append({
            **s,
            "raw": raw,
            "terms": terms,
            "matchable": len(raw) >= MIN_SENTENCE_TOKENS and len(terms) > 0,
        })
    raw_all = tokenize(text)
    return {"raw": raw_all, "terms": normalize(raw_all, settings), "sentences": sentences}


# ---------------------------------------------------------------
# 2. Sentence-level compare
# ---------------------------------------------------------------
def sentence_overlap(raw_a, raw_b):
    """Trigram containment, dono taraf se, jo zyada ho wo. (Copy ke saath extra shabd jude ho tab bhi pakadta hai.)"""
    n = min(3, len(raw_a), len(raw_b))
    if n == 0:
        return 0.0
    set_a, set_b = ngram_set(raw_a, n), ngram_set(raw_b, n)
    return max(containment(set_a, set_b), containment(set_b, set_a))


def label_pair(cosine, overlap, settings):
    if cosine >= settings["near_copy_cosine"] or overlap >= settings["near_copy_ngram"]:
        return "Near-copy"
    if cosine >= settings["similar_cosine"]:
        return "Similar"
    return None


def match_sentences(doc_a, doc_b, settings):
    """Return: (matches, coverage_a_in_b %, coverage_b_in_a %)"""
    a_sents = [s for s in doc_a["sentences"] if s["matchable"]]
    b_sents = [s for s in doc_b["sentences"] if s["matchable"]]
    if not a_sents or not b_sents:
        return [], 0.0, 0.0

    # Corpus = dono documents ke saare sentences; isse IDF nikalta hai
    model = TfidfModel().fit([s["terms"] for s in a_sents + b_sents])
    a_vecs = [model.transform(s["terms"]) for s in a_sents]
    b_vecs = [model.transform(s["terms"]) for s in b_sents]

    # Inverted index: shabd -> B ke kin sentences mein hai (sab pairs compare karne se bachata hai)
    index = {}
    for j, s in enumerate(b_sents):
        for term in set(s["terms"]):
            index.setdefault(term, []).append(j)
    # Bade document mein bahut common shabd (25% se zyada sentences) candidates nahi banate
    limit = len(b_sents) if len(b_sents) <= 40 else int(0.25 * len(b_sents))

    scored = {}                                   # (i, j) -> (cosine, overlap, label)
    for i, s in enumerate(a_sents):
        candidates = set()
        for term in set(s["terms"]):
            postings = index.get(term, [])
            if len(postings) <= limit:
                candidates.update(postings)
        for j in sorted(candidates):
            cos = cosine_similarity(a_vecs[i], b_vecs[j])
            overlap = sentence_overlap(s["raw"], b_sents[j]["raw"])
            label = label_pair(cos, overlap, settings)
            if label:
                scored[(i, j)] = (cos, overlap, label)

    # Har sentence ka sabse achha partner chuno (A->B aur B->A dono taraf se)
    def strength(pair):
        cos, overlap, _ = scored[pair]
        return max(cos, overlap)

    best_for_a, best_for_b = {}, {}
    for (i, j) in scored:
        if i not in best_for_a or strength((i, j)) > strength((i, best_for_a[i])):
            best_for_a[i] = j
        if j not in best_for_b or strength((i, j)) > strength((best_for_b[j], j)):
            best_for_b[j] = i
    chosen = {(i, j) for i, j in best_for_a.items()} | {(i, j) for j, i in best_for_b.items()}

    matches = []
    for (i, j) in sorted(chosen):
        cos, overlap, label = scored[(i, j)]
        a, b = a_sents[i], b_sents[j]
        matches.append({
            "sent_a_text": a["text"], "sent_b_text": b["text"],
            "a_start": a["start"], "a_end": a["end"],
            "b_start": b["start"], "b_end": b["end"],
            "cosine": round(cos, 4), "ngram_overlap": round(overlap, 4), "label": label,
        })
    matches.sort(key=lambda m: m["a_start"])

    coverage_a = 100.0 * len({i for i, _ in chosen}) / len(a_sents)
    coverage_b = 100.0 * len({j for _, j in chosen}) / len(b_sents)
    return matches, coverage_a, coverage_b


# ---------------------------------------------------------------
# 3. Score aur verdict
# ---------------------------------------------------------------
def overall_score(doc_cosine, coverage_percent, settings):
    """Weighted mel: w1 x (cosine x 100) + w2 x coverage. Result 0-100."""
    w1, w2 = settings["weight_cosine"], settings["weight_coverage"]
    total = w1 + w2
    if total <= 0:
        w1, w2, total = 0.5, 0.5, 1.0
    return (w1 * doc_cosine * 100 + w2 * coverage_percent) / total


def verdict_for(score):
    for upper, label in config.VERDICT_BANDS:
        if score < upper:
            return label
    return config.VERDICT_BANDS[-1][1]          # exactly 100


# ---------------------------------------------------------------
# 4. Poora comparison (ek pair)
# ---------------------------------------------------------------
def compare_texts(text_a, text_b, settings=None, library_terms=None):
    """library_terms = library ke baaki documents ke get_terms() (optional, IDF behtar karte hain)."""
    s = merge_settings(settings)
    doc_a = prepare_document(text_a, s)
    doc_b = prepare_document(text_b, s)

    matches, cov_a, cov_b = match_sentences(doc_a, doc_b, s)

    # Document-level cosine: corpus = A + B + library
    corpus = [doc_a["terms"], doc_b["terms"]] + list(library_terms or [])
    model = TfidfModel().fit(corpus)
    doc_cosine = cosine_similarity(model.transform(doc_a["terms"]), model.transform(doc_b["terms"]))

    bigram_jaccard = jaccard(ngram_set(doc_a["raw"], 2), ngram_set(doc_b["raw"], 2))
    trigram_containment = containment(ngram_set(doc_a["raw"], 3), ngram_set(doc_b["raw"], 3))

    score = overall_score(doc_cosine, max(cov_a, cov_b), s)
    return {
        "doc_cosine": round(doc_cosine, 4),
        "bigram_jaccard": round(bigram_jaccard, 4),
        "trigram_containment": round(trigram_containment, 4),
        "coverage_a_in_b": round(cov_a, 2),
        "coverage_b_in_a": round(cov_b, 2),
        "overall_score": round(score, 2),
        "verdict": verdict_for(score),
        "matches": matches,
    }