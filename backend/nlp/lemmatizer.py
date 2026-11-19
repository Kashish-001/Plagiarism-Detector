"""Phase 5a: Lemmatizer (manual): irregular dictionary + suffix rules.
Stemmer se farak: lemma asli shabd hota hai (mice -> mouse, went -> go)."""
from nlp.stemmer import _has_vowel, _measure, _ends_cvc, _ends_double_consonant

# ---------------------------------------------------------------
# 1. Irregular shabd (dictionary lookup)
# ---------------------------------------------------------------
_IRREGULAR = {
    # be / have / do
    "am": "be", "is": "be", "are": "be", "was": "be", "were": "be", "been": "be", "being": "be",
    "has": "have", "had": "have", "having": "have",
    "does": "do", "did": "do", "done": "do", "doing": "do", "goes": "go", "going": "go",
    # irregular verbs
    "went": "go", "gone": "go", "ran": "run", "made": "make", "took": "take", "taken": "take",
    "gave": "give", "given": "give", "came": "come", "wrote": "write", "written": "write",
    "knew": "know", "known": "know", "thought": "think", "found": "find", "told": "tell",
    "became": "become", "began": "begin", "begun": "begin", "brought": "bring", "built": "build",
    "bought": "buy", "caught": "catch", "chose": "choose", "chosen": "choose", "drew": "draw",
    "drawn": "draw", "drove": "drive", "driven": "drive", "ate": "eat", "eaten": "eat",
    "fell": "fall", "fallen": "fall", "flew": "fly", "flown": "fly", "forgot": "forget",
    "got": "get", "gotten": "get", "grew": "grow", "grown": "grow", "held": "hold",
    "kept": "keep", "led": "lead", "lost": "lose", "meant": "mean", "met": "meet",
    "paid": "pay", "said": "say", "sold": "sell", "sent": "send", "shown": "show",
    "sat": "sit", "spoke": "speak", "spoken": "speak", "spent": "spend", "stood": "stand",
    "taught": "teach", "understood": "understand", "won": "win", "wore": "wear", "worn": "wear",
    "threw": "throw", "thrown": "throw", "broke": "break", "broken": "break",
    "sang": "sing", "sung": "sing", "swam": "swim", "used": "use", "died": "die",
    "tied": "tie", "lied": "lie",
    # irregular plurals
    "mice": "mouse", "men": "man", "women": "woman", "children": "child", "feet": "foot",
    "teeth": "tooth", "geese": "goose", "people": "person", "lives": "life", "knives": "knife",
    "wives": "wife", "leaves": "leaf", "halves": "half", "wolves": "wolf", "shelves": "shelf",
    "thieves": "thief", "analyses": "analysis", "crises": "crisis", "theses": "thesis",
    "phenomena": "phenomenon", "criteria": "criterion", "indices": "index",
    "matrices": "matrix", "movies": "movie", "cookies": "cookie",
}

# ---------------------------------------------------------------
# 2. Jin shabdon par rules lagne chahiye hi nahi
# ---------------------------------------------------------------
_PROTECTED = {
    "always", "perhaps", "sometimes", "besides", "towards", "whereas", "series", "species",
    "news", "physics", "mathematics", "economics", "politics", "athletics", "lens", "atlas",
    "canvas", "bias", "christmas", "nothing", "something", "anything", "everything",
    "morning", "evening", "king", "ring", "wing", "sing", "bring", "thing", "spring",
    "string", "ceiling", "hundred", "kindred", "sacred",
}


def _fix_stem(stem):
    """-ing / -ed kaatne ke baad safai: hopp -> hop, mak -> make."""
    if _ends_double_consonant(stem) and stem[-1] not in "lsz":
        return stem[:-1]                    # running -> runn -> run
    if _measure(stem) == 1 and _ends_cvc(stem):
        return stem + "e"                   # making -> mak -> make
    return stem


def lemmatize(word):
    word = word.lower()
    if not word.isalpha():
        return word                         # numbers (2024, 3.5) jaise ke taise

    # Step 1: irregular dictionary
    if word in _IRREGULAR:
        return _IRREGULAR[word]
    if len(word) <= 3 or word in _PROTECTED:
        return word

    # Step 2: plural rules
    if word.endswith("sses"):
        return word[:-2]                    # classes -> class
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"              # studies -> study
    if word.endswith(("xes", "ches", "shes", "zzes")):
        return word[:-2]                    # boxes -> box, churches -> church
    if word.endswith("s") and not word.endswith(("ss", "us", "is", "ous")):
        return word[:-1]                    # words -> word

    # Step 3: -ing
    if word.endswith("ing"):
        stem = word[:-3]
        if len(stem) >= 3 and _has_vowel(stem):
            return _fix_stem(stem)
        return word

    # Step 4: -ed
    if word.endswith("ied") and len(word) > 4:
        return word[:-3] + "y"              # studied -> study
    if word.endswith("eed"):
        return word                         # speed, need
    if word.endswith("ed"):
        stem = word[:-2]
        if len(stem) >= 3 and _has_vowel(stem):
            return _fix_stem(stem)
        return word
    return word


def lemmatize_tokens(tokens):
    return [lemmatize(t) for t in tokens]