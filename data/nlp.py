# === NLP token extraction (single notebook cell) ==============================
# Parses user text into: artists, songs, and k (number of recommendations)
# Safe to re-run; auto-installs the spacy model if missing.

import re
from typing import List, Dict, Any

# ---- spaCy setup -------------------------------------------------------------
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        # model not present in this environment; download once
        import sys, subprocess
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        nlp = spacy.load("en_core_web_sm")
except Exception as e:
    raise RuntimeError(
        "spaCy is required for NER. Try: pip install spacy && python -m spacy download en_core_web_sm"
    ) from e

# ---- normalization helpers ---------------------------------------------------
QUOTE_CHARS = r"\"“”'‘’`"

def _norm_key(s: str) -> str:
    """Normalize for dedupe/compare: strip quotes/spaces, lowercase."""
    if not isinstance(s, str):
        return ""
    return re.sub(f"[{QUOTE_CHARS}]", "", s).lower().strip()

def _split_list(chunk: str) -> List[str]:
    """Split artist/song lists on commas, 'and', ampersands."""
    parts = re.split(r",|\band\b|&", chunk, flags=re.I)
    return [p.strip(" .") for p in parts if p and p.strip(" .")]

# ---- number parsing ----------------------------------------------------------
WORD_NUMS = {
    "one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,
    "eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,"twenty":20
}
APPROX = {"couple":2,"a couple":2,"few":3,"a few":3,"some":5,"several":7}

def _extract_k(text: str, default: int = 10) -> int:
    t = text.lower()

    # explicit digits: "... 7 songs", "top 12", etc.
    m = re.search(r"\b(\d{1,2})\b", t)
    if m:
        return max(1, min(50, int(m.group(1))))

    # phrases like "top 5", "recommend 8"
    m = re.search(r"(top|recommend|suggest|give me|list)\s+(\d{1,2})", t)
    if m:
        return max(1, min(50, int(m.group(2))))

    # words/approximations
    for w, n in WORD_NUMS.items():
        if re.search(rf"\b{re.escape(w)}\b", t):
            return n
    for w, n in APPROX.items():
        if re.search(rf"\b{re.escape(w)}\b", t):
            return n

    return default

# ---- song title detection ----------------------------------------------------
def _extract_quoted_titles(text: str) -> List[str]:
    """Anything inside quotes is taken as a song title."""
    titles = re.findall(rf"[{QUOTE_CHARS}]([^{QUOTE_CHARS}]+)[{QUOTE_CHARS}]", text)
    return [t.strip() for t in titles if t.strip()]

# ---- artist cue extraction ---------------------------------------------------
# We stop artist-capture before words that usually introduce songs/examples.
_CUE_STOP = r"(including|like|such as|feat\.?|featuring|with)\b"

def _cued_after(text: str, cues=("by","from","by artist")) -> List[str]:
    """
    Capture text after cues (by/from/...) up to a stop token or end of line.
    Prevents swallowing 'including "Song"' into artists.
    """
    out = []
    for cue in cues:
        m = re.search(
            rf"\b{re.escape(cue)}\s+([^\.;,\n]+?)(?=\s*{_CUE_STOP}|$)",
            text,
            flags=re.I,
        )
        if m:
            out.extend(_split_list(m.group(1)))
    return out

# ---- dedupe utilities --------------------------------------------------------
def _dedupe_keep_order(items: List[str]) -> List[str]:
    """Dedupe by normalized key while preserving original order; drop empties and overlongs."""
    seen = set(); out = []
    for s in items:
        key = _norm_key(s)
        if not key or len(key) > 100:
            continue
        if key not in seen:
            seen.add(key); out.append(s.strip())
    return out

# ---- main API ----------------------------------------------------------------
def parse_music_query(text: str) -> Dict[str, Any]:
    """
    Returns:
      {
        "artists": [str, ...],
        "songs":   [str, ...],
        "k":       int
      }
    Combines regex cues + quoted titles + spaCy NER for robustness.
    """
    k = _extract_k(text)

    # 1) Songs: quoted or following 'including/like/such as'
    songs = _extract_quoted_titles(text)
    if not songs:
        m = re.search(r"(including|like|such as)\s+(.+)", text, flags=re.I)
        if m:
            songs = _split_list(m.group(2))

    # 2) Artists: follow cues (by/from/...)
    artists = _cued_after(text)

    # 3) NER augmentation
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ("PERSON", "ORG"):       # likely artist
            artists.append(ent.text.strip())
        elif ent.label_ == "WORK_OF_ART":         # likely song
            songs.append(ent.text.strip())

    # 4) Cleanup: remove song strings that leaked into artists (by normalized key)
    song_keys = {_norm_key(s) for s in songs}
    artists = [a for a in artists if _norm_key(a) not in song_keys]

    # 5) Remove pure-numeric items from artists (avoid '"505"' becoming an artist)
    artists = [a for a in artists if not re.fullmatch(r"\d+", _norm_key(a))]

    # 6) Final dedupe (case/quote-insensitive)
    artists = _dedupe_keep_order(artists)
    songs   = _dedupe_keep_order(songs)

    return {"artists": artists, "songs": songs, "k": k}

# ---- quick sanity tests (optional; comment out in production) ----------------
_tests = [
    'give me 5 songs by Drake',
    'recommend a couple of tracks from Taylor Swift including "Cardigan"',
    "top 3 songs like 'Blinding Lights' by The Weeknd",
    'some songs by Bad Bunny',
    'playlist with a few tracks from Beyoncé and Jay-Z',
    'suggest 10 from Arctic Monkeys including "Do I Wanna Know?" and "505"',
]
for q in _tests:
    print(">", q)
    print(parse_music_query(q))
    print("-"*60)
# ==============================================================================
