"""Phase 3: cleaning, sentence splitting, tokenization, stopword removal.
Sab kuch manual (regex + rules). Koi NLP library use nahi hui."""
import os
import re

# ---------------------------------------------------------------
# 1. CLEANER
# ---------------------------------------------------------------
_CHAR_MAP = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u2026": "...",
    "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl",
    "\u00a0": " ", "\u00ad": "", "\u200b": "", "\x00": "",
})

_LINE_ENDINGS = (".", "!", "?", ":", ",", ";")


def _join_lines(paragraph):
    """Ek paragraph ki lines jodta hai. Heading jaisi line alag block ban jati hai."""
    lines = paragraph.split("\n")
    blocks = [lines[0]]
    for line in lines[1:]:
        prev = blocks[-1]
        looks_like_heading = (
            len(prev) < 60
            and not prev.endswith(_LINE_ENDINGS)
            and line[:1].isupper()
        )
        if looks_like_heading:
            blocks.append(line)
        else:
            blocks[-1] = prev + " " + line
    return blocks


def clean_text(text):
    text = text.translate(_CHAR_MAP)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)            # extra spaces -> ek
    text = re.sub(r" ?\n ?", "\n", text)               # newline ke aas-paas ke spaces
    text = re.sub(r"([a-z])-\n([a-z])", r"\1\2", text)  # inter-\nnational -> international
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    blocks = []
    for paragraph in text.split("\n\n"):
        if paragraph.strip():
            blocks.extend(_join_lines(paragraph))
    return "\n\n".join(blocks)


# ---------------------------------------------------------------
# 2. SENTENCE SPLITTER
# ---------------------------------------------------------------
_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "mt", "vs",
    "e.g", "i.e", "cf", "fig", "figs", "eq", "vol", "pp", "al",
    "inc", "ltd", "co", "dept", "approx", "u.s", "u.k", "ph.d",
}
_CLOSERS = "\"')]"
_OPENERS = "\"'(["
_BOUNDARY = re.compile(r"(?P<punct>[.!?]+[\"')\]]*)(?P<ws>\s+)|(?P<para>\n\n)")


def _is_sentence_end(text, m):
    """Punctuation ke baad sach mein sentence khatam hua ya nahi."""
    punct = m.group("punct")

    # Check 1: agla akshar capital / digit / opening quote hona chahiye
    nxt = text[m.end()] if m.end() < len(text) else ""
    if nxt and not (nxt.isupper() or nxt.isdigit() or nxt in _OPENERS):
        return False

    # "!" "?" "..." ke liye itna kaafi hai. Aage sirf single "." ke checks hain.
    if punct.rstrip(_CLOSERS) != ".":
        return True

    before = text[max(0, m.start("punct") - 25):m.start("punct")].split()
    word = before[-1].lstrip(_OPENERS) if before else ""

    # Check 2: abbreviation (Dr., Mr., e.g. ...)
    if word.lower() in _ABBREVIATIONS:
        return False
    # Check 3: initial (J. K. Rowling). "I" ko chhodkar
    if len(word) == 1 and word.isupper() and word != "I":
        return False
    return True


def split_sentences(text):
    """Return: [{"text": ..., "start": ..., "end": ...}, ...]
    start/end text ke andar character positions hain (end exclusive)."""
    sentences = []

    def add(s, e):
        while s < e and text[s].isspace():
            s += 1
        while e > s and text[e - 1].isspace():
            e -= 1
        if e > s:
            sentences.append({"text": text[s:e], "start": s, "end": e})

    start = 0
    for m in _BOUNDARY.finditer(text):
        if m.group("para"):                                   # Check 4: khaali line
            add(start, m.start())
            start = m.end()
        elif "\n\n" in m.group("ws") or _is_sentence_end(text, m):
            add(start, m.end("punct"))
            start = m.end()
    add(start, len(text))
    return sentences


# ---------------------------------------------------------------
# 3. TOKENIZER
# ---------------------------------------------------------------
_TOKEN = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")


def tokenize(text):
    return _TOKEN.findall(text.lower())


# ---------------------------------------------------------------
# 4. STOPWORDS
# ---------------------------------------------------------------
_STOPWORDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stopwords_en.txt")
_stopwords_cache = None


def get_stopwords():
    """File ek baar padhkar set bana leta hai."""
    global _stopwords_cache
    if _stopwords_cache is None:
        words = set()
        with open(_STOPWORDS_FILE, encoding="utf-8") as f:
            for line in f:
                if not line.startswith("#"):
                    words.update(line.lower().split())
        _stopwords_cache = frozenset(words)
    return _stopwords_cache


def remove_stopwords(tokens):
    stop = get_stopwords()
    return [t for t in tokens if t not in stop]