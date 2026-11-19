"""Phase 6a: TF-IDF (manual). Vectors sparse dictionary hain: {term: weight}."""
import math


def term_frequency(tokens):
    """TF = shabd kitni baar aaya / document ke kul shabd.
    ['cat','cat','mat'] -> {'cat': 0.667, 'mat': 0.333}"""
    total = len(tokens)
    if total == 0:
        return {}
    counts = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    return {term: c / total for term, c in counts.items()}


def l2_normalize(vector):
    """Vector ko length 1 par laata hai: har value / sqrt(sum of squares)."""
    length = math.sqrt(sum(w * w for w in vector.values()))
    if length == 0:
        return {}
    return {term: w / length for term, w in vector.items()}


class TfidfModel:
    """fit() corpus se IDF seekhta hai, transform() kisi bhi document ko vector banata hai."""

    def __init__(self):
        self.n_docs = 0
        self.idf = {}

    def _idf_value(self, df):
        # Smoothed IDF: ln((1 + N) / (1 + df)) + 1. Hamesha positive, zero se divide nahi hota.
        return math.log((1 + self.n_docs) / (1 + df)) + 1

    def fit(self, docs_tokens):
        """docs_tokens = [[token, ...], [token, ...], ...]"""
        self.n_docs = len(docs_tokens)
        df = {}
        for tokens in docs_tokens:
            for term in set(tokens):            # set: ek document mein ek baar hi ginna
                df[term] = df.get(term, 0) + 1
        self.idf = {term: self._idf_value(count) for term, count in df.items()}
        return self

    def transform(self, tokens):
        """TF x IDF, phir L2 normalize. Naya shabd (corpus mein nahi) ko sabse zyada IDF milta hai."""
        unseen_idf = self._idf_value(0)
        tf = term_frequency(tokens)
        vector = {term: weight * self.idf.get(term, unseen_idf) for term, weight in tf.items()}
        return l2_normalize(vector)

    def fit_transform(self, docs_tokens):
        self.fit(docs_tokens)
        return [self.transform(tokens) for tokens in docs_tokens]