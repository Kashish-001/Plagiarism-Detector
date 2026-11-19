"""Phase 5b: N-grams aur overlap measures (manual)."""


def generate_ngrams(tokens, n):
    """['the','cat','sat'], n=2 -> [('the','cat'), ('cat','sat')]"""
    if n < 1:
        raise ValueError("n must be at least 1")
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def ngram_set(tokens, n):
    return set(generate_ngrams(tokens, n))


def ngram_frequencies(tokens, n):
    """Har n-gram kitni baar aaya: {('the','cat'): 2, ...}"""
    counts = {}
    for gram in generate_ngrams(tokens, n):
        counts[gram] = counts.get(gram, 0) + 1
    return counts


def top_ngrams(tokens, n, k=10):
    """Sabse zyada aane wale k n-grams, [(gram, count), ...]"""
    counts = ngram_frequencies(tokens, n)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:k]


def jaccard(set_a, set_b):
    """|A ∩ B| / |A ∪ B|. Symmetric: A aur B ka order matter nahi karta."""
    union = len(set_a | set_b)
    if union == 0:
        return 0.0
    return len(set_a & set_b) / union


def containment(set_a, set_b):
    """|A ∩ B| / |A|: A ka kitna hissa B mein mila. Asymmetric (copy pakadne ke liye)."""
    if len(set_a) == 0:
        return 0.0
    return len(set_a & set_b) / len(set_a)