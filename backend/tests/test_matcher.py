from nlp.matcher import (compare_texts, get_terms, label_pair, merge_settings,
                         overall_score, verdict_for)

TEXT_A = (
    "Climate change is one of the most pressing issues of our time. "
    "Rising global temperatures are causing sea levels to rise and weather patterns to shift. "
    "Many governments have set targets to cut emissions. "
    "Renewable energy now supplies a growing share of electricity. "
    "Further research is needed on storage."
)
TEXT_B = (
    "The report begins with a short history of energy policy. "
    "Rising global temperatures are causing sea levels to rise and weather patterns to shift. "
    "Targets differ widely between countries. "
    "A growing share of electricity is now supplied by renewable sources."
)
UNRELATED = (
    "Photosynthesis converts sunlight into chemical energy inside the chloroplasts of green plants. "
    "Mitochondria produce most of the energy that animal cells need."
)
DB_KEYS = {"doc_cosine", "bigram_jaccard", "trigram_containment", "coverage_a_in_b",
           "coverage_b_in_a", "overall_score", "verdict", "matches"}
MATCH_KEYS = {"sent_a_text", "sent_b_text", "a_start", "a_end", "b_start", "b_end",
              "cosine", "ngram_overlap", "label"}


def test_identical_documents_score_100():
    r = compare_texts(TEXT_A, TEXT_A)
    assert r["overall_score"] == 100.0
    assert r["verdict"] == "Very High"
    assert r["coverage_a_in_b"] == 100.0


def test_unrelated_documents_score_low():
    r = compare_texts(TEXT_A, UNRELATED)
    assert r["matches"] == []
    assert r["verdict"] == "Low"


def test_copied_sentence_is_near_copy():
    r = compare_texts(TEXT_A, TEXT_B)
    labels = {m["sent_a_text"][:6]: m["label"] for m in r["matches"]}
    assert labels["Rising"] == "Near-copy"


def test_reworded_sentence_is_similar():
    r = compare_texts(TEXT_A, TEXT_B)
    labels = {m["sent_a_text"][:9]: m["label"] for m in r["matches"]}
    assert labels["Renewable"] == "Similar"


def test_match_offsets_point_to_original_text():
    r = compare_texts(TEXT_A, TEXT_B)
    assert len(r["matches"]) >= 2
    for m in r["matches"]:
        assert TEXT_A[m["a_start"]:m["a_end"]] == m["sent_a_text"]
        assert TEXT_B[m["b_start"]:m["b_end"]] == m["sent_b_text"]


def test_result_has_all_fields_the_database_needs():
    r = compare_texts(TEXT_A, TEXT_B)
    assert set(r) == DB_KEYS
    for m in r["matches"]:
        assert set(m) == MATCH_KEYS


def test_short_sentences_are_ignored():
    r = compare_texts("Yes. No. Maybe.", "Yes. No. Maybe.")
    assert r["matches"] == []
    assert r["coverage_a_in_b"] == 0.0


def test_higher_threshold_removes_similar_match():
    r = compare_texts(TEXT_A, TEXT_B, {"similar_cosine": 0.95})
    assert all(m["label"] == "Near-copy" for m in r["matches"])


def test_library_terms_are_accepted():
    library = [get_terms(UNRELATED), get_terms("Cats sleep on warm mats during the afternoon.")]
    r = compare_texts(TEXT_A, TEXT_B, library_terms=library)
    assert 0.0 <= r["doc_cosine"] <= 1.0


def test_overall_score_formula():
    s = merge_settings({"weight_cosine": 0.5, "weight_coverage": 0.5})
    assert overall_score(0.5, 80, s) == 65.0
    only_cosine = merge_settings({"weight_cosine": 1.0, "weight_coverage": 0.0})
    assert overall_score(1.0, 0, only_cosine) == 100.0


def test_verdict_bands():
    assert verdict_for(10) == "Low"
    assert verdict_for(25) == "Moderate"
    assert verdict_for(49.9) == "Moderate"
    assert verdict_for(50) == "High"
    assert verdict_for(75) == "Very High"
    assert verdict_for(100) == "Very High"


def test_label_rules():
    s = merge_settings(None)
    assert label_pair(0.90, 0.0, s) == "Near-copy"
    assert label_pair(0.10, 0.80, s) == "Near-copy"
    assert label_pair(0.70, 0.10, s) == "Similar"
    assert label_pair(0.30, 0.10, s) is None