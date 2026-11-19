import pytest

from nlp.preprocessing import clean_text, split_sentences, tokenize, remove_stopwords
from nlp.stemmer import stem, stem_tokens


# ---------------- Phase 3: preprocessing ----------------
def test_clean_fixes_hyphenation():
    assert clean_text("inter-\nnational trade") == "international trade"


def test_clean_joins_wrapped_lines():
    text = "This is a long line that wraps in the middle of a sentence and\ncontinues here."
    assert "\n" not in clean_text(text)


def test_clean_keeps_heading_separate():
    assert clean_text("Introduction\nClimate change is real.") == "Introduction\n\nClimate change is real."


def test_split_handles_abbreviations():
    text = "Dr. Smith went to Washington. He met Mr. Jones at 3.30 p.m. They talked about e.g. climate change."
    s = split_sentences(text)
    assert len(s) == 3
    assert s[0]["text"] == "Dr. Smith went to Washington."


def test_split_offsets_match_original_text():
    text = "First one. Second one? Third one!"
    result = split_sentences(text)
    assert len(result) == 3
    for s in result:
        assert text[s["start"]:s["end"]] == s["text"]


def test_tokenize():
    assert tokenize("Don't stop: U.S. growth was 3.5% in 2024!") == [
        "don", "t", "stop", "u", "s", "growth", "was", "3.5", "in", "2024"]


def test_remove_stopwords():
    assert remove_stopwords(["the", "cat", "is", "on", "the", "mat"]) == ["cat", "mat"]


# ---------------- Phase 4: Porter stemmer ----------------
STEMMER_CASES = [
    # step 1a
    ("caresses", "caress"), ("ponies", "poni"), ("ties", "ti"), ("caress", "caress"), ("cats", "cat"),
    # step 1b
    ("feed", "feed"), ("agreed", "agre"), ("plastered", "plaster"), ("bled", "bled"),
    ("motoring", "motor"), ("sing", "sing"), ("conflated", "conflat"), ("troubled", "troubl"),
    ("hopping", "hop"), ("tanned", "tan"), ("falling", "fall"), ("hissing", "hiss"),
    ("filing", "file"),
    # step 1c
    ("happy", "happi"), ("sky", "sky"),
    # step 2
    ("relational", "relat"), ("conditional", "condit"), ("rational", "ration"),
    ("digitizer", "digit"), ("operator", "oper"), ("feudalism", "feudal"),
    ("decisiveness", "decis"), ("hopefulness", "hope"), ("sensitiviti", "sensit"),
    # step 3
    ("triplicate", "triplic"), ("formative", "form"), ("electrical", "electr"),
    ("hopeful", "hope"), ("goodness", "good"),
    # step 4
    ("revival", "reviv"), ("allowance", "allow"), ("inference", "infer"),
    ("adjustable", "adjust"), ("replacement", "replac"), ("adjustment", "adjust"),
    ("dependent", "depend"), ("adoption", "adopt"), ("communism", "commun"),
    ("effective", "effect"),
    # step 5
    ("probate", "probat"), ("rate", "rate"), ("cease", "ceas"), ("controll", "control"),
    # ek hi root par aane chahiye
    ("running", "run"), ("runs", "run"), ("studies", "studi"), ("generalization", "gener"),
]


@pytest.mark.parametrize("word,expected", STEMMER_CASES)
def test_stem_known_words(word, expected):
    assert stem(word) == expected


def test_stem_leaves_short_words_and_numbers():
    assert stem("is") == "is"
    assert stem("2024") == "2024"
    assert stem("3.5") == "3.5"


def test_stem_tokens_list():
    assert stem_tokens(["running", "runs", "cats"]) == ["run", "run", "cat"]