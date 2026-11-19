"""Phase 6b: Cosine similarity (manual) sparse vectors par."""
import math


def dot_product(vec_a, vec_b):
    """Sirf common shabdon ka guna-jod. Chhote dictionary par loop chalate hain (tez)."""
    if len(vec_a) > len(vec_b):
        vec_a, vec_b = vec_b, vec_a
    return sum(w * vec_b[term] for term, w in vec_a.items() if term in vec_b)


def vector_length(vec):
    return math.sqrt(sum(w * w for w in vec.values()))


def cosine_similarity(vec_a, vec_b):
    """cos = (A . B) / (|A| x |B|). Result 0 (bilkul alag) se 1 (bilkul same)."""
    len_a = vector_length(vec_a)
    len_b = vector_length(vec_b)
    if len_a == 0 or len_b == 0:
        return 0.0
    score = dot_product(vec_a, vec_b) / (len_a * len_b)
    return max(0.0, min(1.0, score))            # float ki chhoti galtiyan (1.0000000002) theek karo