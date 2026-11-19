"""Phase 4: Porter Stemmer (1980),"""

# ---------------------------------------------------------------
# Helpers: consonant / vowel / measure
# ---------------------------------------------------------------
def _is_consonant(word, i):
    ch = word[i]
    if ch in "aeiou":
        return False
    if ch == "y":
        # 'y' pehla akshar ho ya pichhla akshar vowel ho to consonant, warna vowel
        return i == 0 or not _is_consonant(word, i - 1)
    return True


def _measure(stem):
    """m = stem mein 'vowel ke baad consonant' ke kitne jode hain.
    tree -> 0, trouble -> 1, private -> 2"""
    m = 0
    prev_was_vowel = False
    for i in range(len(stem)):
        if _is_consonant(stem, i):
            if prev_was_vowel:
                m += 1
            prev_was_vowel = False
        else:
            prev_was_vowel = True
    return m


def _has_vowel(stem):
    return any(not _is_consonant(stem, i) for i in range(len(stem)))


def _ends_double_consonant(word):
    return len(word) >= 2 and word[-1] == word[-2] and _is_consonant(word, len(word) - 1)


def _ends_cvc(word):
    """consonant-vowel-consonant, aur aakhri akshar w, x, y na ho (hop, fil, ...)."""
    n = len(word)
    return (
        n >= 3
        and _is_consonant(word, n - 3)
        and not _is_consonant(word, n - 2)
        and _is_consonant(word, n - 1)
        and word[-1] not in "wxy"
    )


def _replace_suffix(word, rules, min_measure):
    """rules = [(suffix, replacement)]. Sabse lamba matching suffix chunte hain.
    Condition (measure > min_measure) fail ho to word waisa hi rehta hai."""
    for suffix, replacement in sorted(rules, key=lambda r: len(r[0]), reverse=True):
        if word.endswith(suffix):
            stem = word[: -len(suffix)]
            if _measure(stem) > min_measure:
                return stem + replacement
            return word
    return word


# ---------------------------------------------------------------
# Step 1a: plurals
# ---------------------------------------------------------------
def _step1a(word):
    if word.endswith("sses"):
        return word[:-2]            # caresses -> caress
    if word.endswith("ies"):
        return word[:-2]            # ponies -> poni
    if word.endswith("ss"):
        return word                 # caress -> caress
    if word.endswith("s"):
        return word[:-1]            # cats -> cat
    return word


# ---------------------------------------------------------------
# Step 1b: -ed, -ing
# ---------------------------------------------------------------
def _step1b(word):
    if word.endswith("eed"):
        if _measure(word[:-3]) > 0:
            return word[:-1]        # agreed -> agree
        return word

    for suffix in ("ed", "ing"):
        if word.endswith(suffix):
            stem = word[: -len(suffix)]
            if not _has_vowel(stem):
                return word         # sing, bled: stem mein vowel nahi, kuch nahi karna
            word = stem
            # kaatne ke baad safai
            if word.endswith(("at", "bl", "iz")):
                return word + "e"   # conflat -> conflate
            if _ends_double_consonant(word) and word[-1] not in "lsz":
                return word[:-1]    # hopp -> hop
            if _measure(word) == 1 and _ends_cvc(word):
                return word + "e"   # fil -> file
            return word
    return word


# ---------------------------------------------------------------
# Step 1c: y -> i
# ---------------------------------------------------------------
def _step1c(word):
    if word.endswith("y") and _has_vowel(word[:-1]):
        return word[:-1] + "i"      # happy -> happi, sky -> sky
    return word


# ---------------------------------------------------------------
# Steps 2, 3, 4: suffix rules
# ---------------------------------------------------------------
_STEP2 = [
    ("ational", "ate"), ("tional", "tion"), ("enci", "ence"), ("anci", "ance"),
    ("izer", "ize"), ("bli", "ble"), ("alli", "al"), ("entli", "ent"),
    ("eli", "e"), ("ousli", "ous"), ("ization", "ize"), ("ation", "ate"),
    ("ator", "ate"), ("alism", "al"), ("iveness", "ive"), ("fulness", "ful"),
    ("ousness", "ous"), ("aliti", "al"), ("iviti", "ive"), ("biliti", "ble"),
    ("logi", "log"),
]

_STEP3 = [
    ("icate", "ic"), ("ative", ""), ("alize", "al"), ("iciti", "ic"),
    ("ical", "ic"), ("ful", ""), ("ness", ""),
]

_STEP4 = [
    "al", "ance", "ence", "er", "ic", "able", "ible", "ant", "ement", "ment",
    "ent", "ion", "ou", "ism", "ate", "iti", "ous", "ive", "ize",
]


def _step2(word):
    return _replace_suffix(word, _STEP2, 0)


def _step3(word):
    return _replace_suffix(word, _STEP3, 0)


def _step4(word):
    for suffix in sorted(_STEP4, key=len, reverse=True):
        if word.endswith(suffix):
            stem = word[: -len(suffix)]
            if suffix == "ion" and not stem.endswith(("s", "t")):
                return word
            if _measure(stem) > 1:
                return stem
            return word
    return word


# ---------------------------------------------------------------
# Step 5: aakhri safai
# ---------------------------------------------------------------
def _step5(word):
    # 5a: aakhri 'e' hatana
    if word.endswith("e"):
        stem = word[:-1]
        m = _measure(stem)
        if m > 1 or (m == 1 and not _ends_cvc(stem)):
            word = stem             # probate -> probat, rate -> rate
    # 5b: 'll' -> 'l'
    if _measure(word) > 1 and _ends_double_consonant(word) and word.endswith("l"):
        word = word[:-1]            # controll -> control
    return word


# ---------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------
def stem(word):
    word = word.lower()
    if len(word) <= 2 or not word.isalpha():
        return word                 # chhote shabd aur numbers (2024, 3.5) jaise ke taise
    word = _step1a(word)
    word = _step1b(word)
    word = _step1c(word)
    word = _step2(word)
    word = _step3(word)
    word = _step4(word)
    word = _step5(word)
    return word


def stem_tokens(tokens):
    return [stem(t) for t in tokens]