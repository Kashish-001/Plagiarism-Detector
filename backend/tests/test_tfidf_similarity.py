import math

import numpy as np

from nlp.tfidf import TfidfModel, term_frequency
from nlp.similarity import cosine_similarity

DOCS = [["cat", "sat", "mat"], ["cat", "sat", "hat"], ["dog", "ran", "far"]]


def test_term_frequency():
    tf = term_frequency(["cat", "cat", "mat"])
    assert math.isclose(tf["cat"], 2 / 3)
    assert math.isclose(tf["mat"], 1 / 3)


def test_term_frequency_empty():
    assert term_frequency([]) == {}


def test_idf_matches_formula():
    model = TfidfModel().fit(DOCS)
    assert math.isclose(model.idf["cat"], math.log(4 / 3) + 1)
    assert math.isclose(model.idf["mat"], math.log(4 / 2) + 1)


def test_rare_word_has_higher_idf():
    model = TfidfModel().fit(DOCS)
    assert model.idf["mat"] > model.idf["cat"]


def test_word_in_every_document_still_positive():
    model = TfidfModel().fit([["a", "b"], ["a", "c"]])
    assert model.idf["a"] > 0


def test_repeated_word_counts_once_for_df():
    model = TfidfModel().fit([["a", "a", "a"], ["b"]])
    assert math.isclose(model.idf["a"], math.log(3 / 2) + 1)


def test_unseen_word_gets_highest_idf():
    model = TfidfModel().fit(DOCS)
    assert model.transform(["zebra"]) == {"zebra": 1.0}
    assert model._idf_value(0) > max(model.idf.values())


def test_vectors_have_length_one():
    vectors = TfidfModel().fit_transform(DOCS)
    for v in vectors:
        assert math.isclose(math.sqrt(sum(w * w for w in v.values())), 1.0)


def test_identical_documents_give_one():
    v = TfidfModel().fit_transform(DOCS)
    assert math.isclose(cosine_similarity(v[0], v[0]), 1.0)


def test_disjoint_documents_give_zero():
    v = TfidfModel().fit_transform(DOCS)
    assert cosine_similarity(v[0], v[2]) == 0.0


def test_empty_vector_gives_zero():
    assert cosine_similarity({}, {"a": 1.0}) == 0.0


def test_cosine_is_symmetric():
    v = TfidfModel().fit_transform(DOCS)
    assert math.isclose(cosine_similarity(v[0], v[1]), cosine_similarity(v[1], v[0]))


def test_known_value():
    v = TfidfModel().fit_transform(DOCS)
    assert math.isclose(cosine_similarity(v[0], v[1]), 0.53635, abs_tol=1e-4)


def test_matches_numpy():
    v = TfidfModel().fit_transform(DOCS)
    terms = sorted({t for d in DOCS for t in d})
    a = np.array([v[0].get(t, 0) for t in terms])
    b = np.array([v[1].get(t, 0) for t in terms])
    expected = a @ b / (np.linalg.norm(a) * np.linalg.norm(b))
    assert math.isclose(cosine_similarity(v[0], v[1]), expected)