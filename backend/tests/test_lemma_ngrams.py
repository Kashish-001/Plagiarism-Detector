import pytest

from nlp.lemmatizer import lemmatize, lemmatize_tokens
from nlp.ngrams import (generate_ngrams, ngram_frequencies, top_ngrams,
                        jaccard, containment)

LEMMA_CASES = [
    ("mice", "mouse"), ("went", "go"), ("children", "child"),
    ("studies", "study"), ("studied", "study"), ("studying", "study"),
    ("running", "run"), ("stopped", "stop"), ("making", "make"), ("hoping", "hope"),
    ("writing", "write"), ("visiting", "visit"), ("reading", "read"),
    ("opening", "open"), ("falling", "fall"),
    ("classes", "class"), ("boxes", "box"), ("churches", "church"),
    ("words", "word"), ("cats", "cat"),
    ("this", "this"), ("analysis", "analysis"), ("business", "business"),
    ("news", "news"), ("nothing", "nothing"),
    ("speed", "speed"), ("based", "base"), ("looked", "look"), ("building", "build"),
    ("was", "be"), ("has", "have"), ("2024", "2024"),
]


@pytest.mark.parametrize("word,expected", LEMMA_CASES)
def test_lemmatize(word, expected):
    assert lemmatize(word) == expected


def test_lemmatize_tokens():
    assert lemmatize_tokens(["mice", "went", "studies"]) == ["mouse", "go", "study"]


def test_generate_bigrams():
    tokens = ["the", "cat", "sat", "on", "the", "mat"]
    assert generate_ngrams(tokens, 2) == [
        ("the", "cat"), ("cat", "sat"), ("sat", "on"), ("on", "the"), ("the", "mat")]


def test_ngrams_longer_than_text_is_empty():
    assert generate_ngrams(["a", "b"], 3) == []


def test_ngram_size_must_be_positive():
    with pytest.raises(ValueError):
        generate_ngrams(["a", "b"], 0)


def test_ngram_frequencies_and_top():
    tokens = ["a", "b", "a", "b", "a"]
    assert ngram_frequencies(tokens, 1) == {("a",): 3, ("b",): 2}
    assert top_ngrams(tokens, 1, k=1) == [(("a",), 3)]


def test_jaccard_is_symmetric():
    a, b = {1, 2, 3}, {2, 3, 4}
    assert jaccard(a, b) == 0.5
    assert jaccard(b, a) == 0.5


def test_containment_is_not_symmetric():
    a, b = {1, 2, 3}, {1, 2, 3, 4, 5, 6}
    assert containment(a, b) == 1.0
    assert containment(b, a) == 0.5


def test_empty_sets_give_zero():
    assert jaccard(set(), set()) == 0.0
    assert containment(set(), {1}) == 0.0