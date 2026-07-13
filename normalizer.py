from __future__ import annotations
import re
from typing import Any, NamedTuple

from books import BOOKS
from spoken_numbers import normalize_spoken_numbers, NUMBER_WORDS, DIGIT_ORD_PATTERN


class Token(NamedTuple):
    type: str
    text: str
    value: Any = None


CORRECTION_WORDS = {"కాదు", "సారీ", "no", "sorry", "ఆ", "aa"}

CHAPTER_WORDS = {"అధ్యాయం", "అధ్యాయము", "chapter", "chapters", "ch"}
VERSE_WORDS = {"వచనం", "వచనము", "వచనాలు", "verse", "verses", "v"}

IGNORE_WORDS = {
    "వ్రాసిన", "గ్రంథము", "గ్రంథం", "పుస్తకము", "పుస్తకం", "పత్రిక", "సువార్త",
    "మనము", "ఇప్పుడు", "చూద్దాం", "తిరగండి", "కొంచెం", "ఒక్కసారి", "దయచేసి", "వెళ్దాం", "అంటే",
    "నుంచి", "వరకు", "nunchi", "varaku",
    "and", "the", "of", "to", "in", "is", "am",
    "udayakalamlo", "manamandaramu", "manamandaram", "priyularaa",
    "terichinatlayite", "terichinatlu", "ayithe",
    "ee", "oka", "kani", "appudu", "akkaDa",
    "ila", "sarE", "kaasta", "intha",
    "taruvaata", "mundu",
}

_SINGLE_BOOK_MAP: dict[str, str] = {}
_NUMBERED_BASE: dict[str, dict[int, str]] = {}

_NUM_PREFIX = {"1", "2", "3", "first", "second", "third",
               "మొదటి", "రెండవ", "మూడవ"}


def _num_val(w: str) -> int | None:
    d = {"1": 1, "2": 2, "3": 3, "first": 1, "second": 2, "third": 3,
         "మొదటి": 1, "రెండవ": 2, "మూడవ": 3}
    return d.get(w.lower())


for entry in BOOKS:
    canon = entry.canonical
    for alias in entry.aliases:
        words = alias.split()
        if len(words) == 1:
            _SINGLE_BOOK_MAP[words[0].lower()] = canon
        elif len(words) >= 2:
            nv = _num_val(words[0])
            if nv is not None:
                base = " ".join(words[1:]).lower()
                if base not in _SINGLE_BOOK_MAP:
                    _SINGLE_BOOK_MAP[base] = canon
                if base not in _NUMBERED_BASE:
                    _NUMBERED_BASE[base] = {}
                _NUMBERED_BASE[base][nv] = canon

ROMANIZED_LOOKUP: dict[str, str] = {
    "aadikaandamu": "Genesis",
    "aadikandamu": "Genesis",
    "aadikaandam": "Genesis",
    "aadikandam": "Genesis",
    "aadi": "Genesis",
    "nirgamakaandamu": "Exodus",
    "nirgamakandamu": "Exodus",
    "nirgamakaandam": "Exodus",
    "nirgama": "Exodus",
    "leveeyakaandamu": "Leviticus",
    "leveeyakandamu": "Leviticus",
    "samkhyaakaandamu": "Numbers",
    "samkhyakandamu": "Numbers",
    "dviteeyopadeshakaandamu": "Deuteronomy",
    "dviteeyopadeshakandamu": "Deuteronomy",
    "dviteeyo": "Deuteronomy",
    "yehoshuv": "Joshua",
    "yehoshuva": "Joshua",
    "yeho": "Joshua",
    "nyaayaadhipatulu": "Judges",
    "nyaayadhipatulu": "Judges",
    "rootu": "Ruth",
    "samooyelu": "1 Samuel",
    "samuyelu": "1 Samuel",
    "raajulu": "1 Kings",
    "rajulu": "1 Kings",
    "dinavruttaamtamulu": "1 Chronicles",
    "dinavruttamtamulu": "1 Chronicles",
    "ejra": "Ezra",
    "ejraa": "Ezra",
    "nehemya": "Nehemiah",
    "nehemyaa": "Nehemiah",
    "esteru": "Esther",
    "yobu": "Job",
    "keerthanalu": "Psalms",
    "kirthanalu": "Psalms",
    "keerthan": "Psalms",
    "keerthana": "Psalms",
    "saametalu": "Proverbs",
    "sametalu": "Proverbs",
    "prasamgi": "Ecclesiastes",
    "paramageetamu": "Song of Solomon",
    "paramagitamu": "Song of Solomon",
    "yeshaya": "Isaiah",
    "yeshayaa": "Isaiah",
    "yirmiya": "Jeremiah",
    "yirmiyaa": "Jeremiah",
    "vilaapavaakyamulu": "Lamentations",
    "vilapavakyamulu": "Lamentations",
    "yehejkelu": "Ezekiel",
    "yehejkel": "Ezekiel",
    "daaniyelu": "Daniel",
    "daniyelu": "Daniel",
    "hoseya": "Hosea",
    "hosheya": "Hosea",
    "yovelu": "Joel",
    "aamosu": "Amos",
    "amosu": "Amos",
    "obadya": "Obadiah",
    "obadyaa": "Obadiah",
    "yona": "Jonah",
    "yonaa": "Jonah",
    "meeka": "Micah",
    "meekaa": "Micah",
    "nahoomu": "Nahum",
    "nahumu": "Nahum",
    "habakkooku": "Habakkuk",
    "habakkuku": "Habakkuk",
    "jepanyaa": "Zephaniah",
    "jephanya": "Zephaniah",
    "haggayi": "Haggai",
    "jekarya": "Zechariah",
    "jekaryaa": "Zechariah",
    "malaakee": "Malachi",
    "malaaki": "Malachi",
    "mattayi": "Matthew",
    "matta": "Matthew",
    "maarku": "Mark",
    "marku": "Mark",
    "looka": "Luke",
    "lookaa": "Luke",
    "yohaanu": "John",
    "yohanu": "John",
    "apostalulakaaryamulu": "Acts",
    "apostalulakaryamulu": "Acts",
    "romiyulaku": "Romans",
    "romeeyulaku": "Romans",
    "korimtheeyulaku": "1 Corinthians",
    "korimthiyulaku": "1 Corinthians",
    "galateeyulaku": "Galatians",
    "galatiyulaku": "Galatians",
    "epheseeyulaku": "Ephesians",
    "ephesiyulaku": "Ephesians",
    "philippeeyulaku": "Philippians",
    "philippiyulaku": "Philippians",
    "kolossayulaku": "Colossians",
    "tessaloneekayulaku": "1 Thessalonians",
    "timotiki": "1 Timothy",
    "teetuku": "Titus",
    "tituku": "Titus",
    "philemonuku": "Philemon",
    "pilemonuku": "Philemon",
    "hebreeyulaku": "Hebrews",
    "hebriyulaku": "Hebrews",
    "yaakobu": "James",
    "yakobu": "James",
    "peturu": "1 Peter",
    "yooda": "Jude",
    "yudaa": "Jude",
    "prakatan": "Revelation",
    "prakatana": "Revelation",
    "praka": "Revelation",
}

for roman, canon in ROMANIZED_LOOKUP.items():
    if roman not in _SINGLE_BOOK_MAP:
        _SINGLE_BOOK_MAP[roman] = canon

TELUGU_SUFFIXES = ("కు", "కి", "నకు", "ల")


def _strip_suffix(word: str) -> str:
    for s in TELUGU_SUFFIXES:
        if word.endswith(s) and len(word) > len(s) + 1:
            return word[: -len(s)]
    return word


def _single_book_lookup(word: str) -> str | None:
    raw = word.lower()
    canon = _SINGLE_BOOK_MAP.get(raw)
    if canon is not None:
        return canon
    stripped = _strip_suffix(raw)
    if stripped != raw:
        return _SINGLE_BOOK_MAP.get(stripped)
    return None


def _resolve_numbered(num: int, canon: str) -> str | None:
    m = re.match(r"^\d+\s+(.+)", canon)
    base = m.group(1).lower() if m else canon.lower()
    nd = _NUMBERED_BASE.get(base)
    if nd and num in nd:
        return nd[num]
    return None


TOKEN_RE = re.compile(r"[\w\u0C00-\u0C7F]+|[:\-]")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def _is_number_token(t: str) -> bool:
    tl = t.lower()
    return tl.isdigit() or tl in NUMBER_WORDS or bool(DIGIT_ORD_PATTERN.match(t))


def classify(tokens: list[str]) -> list[Token]:
    result: list[Token] = []
    for i, t in enumerate(tokens):
        t_lower = t.lower()
        if t_lower in CORRECTION_WORDS:
            if t_lower in ("ఆ", "aa"):
                prev_is_number = i > 0 and _is_number_token(tokens[i - 1])
                next_is_number = i + 1 < len(tokens) and _is_number_token(tokens[i + 1])
                prev_is_book = i > 0 and _single_book_lookup(tokens[i - 1]) is not None
                if prev_is_number:
                    pass
                elif prev_is_book:
                    result.append(Token("IGNORE", t))
                    continue
                elif not next_is_number:
                    result.append(Token("IGNORE", t))
                    continue
            result.append(Token("CORRECTION", t))
        elif t_lower in CHAPTER_WORDS:
            result.append(Token("CHAPTER", t))
        elif t_lower in VERSE_WORDS:
            result.append(Token("VERSE", t))
        elif t_lower in IGNORE_WORDS:
            result.append(Token("IGNORE", t))
        elif t_lower in (":", "-"):
            result.append(Token("IGNORE", t))
        elif t.isdigit():
            result.append(Token("NUMBER", t, int(t)))
        elif t_lower in NUMBER_WORDS:
            result.append(Token("NUMBER", t, NUMBER_WORDS[t_lower]))
        else:
            m = DIGIT_ORD_PATTERN.match(t)
            if m:
                result.append(Token("NUMBER", t, int(m.group(1))))
            else:
                canon = _single_book_lookup(t)
                if canon is not None:
                    result.append(Token("BOOK", t, canon))
                else:
                    result.append(Token("UNKNOWN", t))
    return result


def parse(tokens: list[Token]) -> str:
    book: str | None = None
    chapter: int | None = None
    verse: int | None = None
    end_verse: int | None = None
    book_prefix: int | None = None
    pending_chapter = False
    pending_verse = False
    correction_just_happened = False

    i = 0
    while i < len(tokens):
        tok = tokens[i]

        if tok.type in ("IGNORE", "UNKNOWN"):
            i += 1
            continue

        if tok.type == "CORRECTION":
            if end_verse is not None:
                end_verse = None
            elif verse is not None:
                verse = None
                correction_just_happened = True
            elif chapter is not None:
                chapter = None
            elif book is not None:
                book = None
                book_prefix = None
            pending_chapter = False
            pending_verse = False
            i += 1
            continue

        if tok.type == "CHAPTER":
            if book_prefix is not None:
                chapter = book_prefix
                book_prefix = None
                pending_chapter = False
            elif chapter is None:
                pending_chapter = True
            pending_verse = False
            correction_just_happened = False
            i += 1
            continue

        if tok.type == "VERSE":
            if verse is None:
                pending_verse = True
            pending_chapter = False
            correction_just_happened = False
            i += 1
            continue

        if tok.type == "NUMBER":
            val = tok.value

            if correction_just_happened:
                correction_just_happened = False
                has_next_number = False
                for j in range(i + 1, min(i + 4, len(tokens))):
                    if tokens[j].type == "NUMBER":
                        has_next_number = True
                        break
                    elif tokens[j].type in ("CHAPTER", "VERSE"):
                        continue
                    elif tokens[j].type in ("IGNORE", "UNKNOWN"):
                        continue
                    else:
                        break

                if has_next_number:
                    chapter = val
                else:
                    if chapter is not None:
                        verse = val
                    else:
                        chapter = val
                i += 1
                continue

            if pending_chapter:
                chapter = val
                pending_chapter = False
            elif pending_verse:
                verse = val
                pending_verse = False
            elif book_prefix is not None:
                chapter = book_prefix
                book_prefix = None
                if chapter is not None:
                    if verse is None:
                        verse = val
                    else:
                        end_verse = val
                else:
                    chapter = val
            elif book is None:
                book_prefix = val
            elif chapter is None:
                chapter = val
            elif verse is None:
                verse = val
            else:
                end_verse = val
            i += 1
            continue

        if tok.type == "BOOK":
            if book_prefix is not None:
                base_match = re.match(r"^\d+\s+(.+)", tok.value)
                base = base_match.group(1).lower() if base_match else None
                nd = _NUMBERED_BASE.get(base) if base else _NUMBERED_BASE.get(tok.value.lower())
                if nd and book_prefix in nd:
                    book = nd[book_prefix]
                else:
                    chapter = book_prefix
                    book = tok.value
                book_prefix = None
            else:
                book = tok.value
                chapter = None
                verse = None
                end_verse = None
            pending_chapter = False
            pending_verse = False
            correction_just_happened = False
            i += 1
            continue

        i += 1

    if book_prefix is not None and chapter is None:
        chapter = book_prefix
        book_prefix = None

    parts: list[str] = []
    if book:
        parts.append(book)
    if chapter is not None:
        parts.append(str(chapter))
    if verse is not None:
        parts.append(str(verse))
    if end_verse is not None:
        parts.append(str(end_verse))

    if not parts:
        if chapter is not None:
            parts.append(str(chapter))
        if verse is not None:
            parts.append(str(verse))
        if end_verse is not None:
            parts.append(str(end_verse))

    return " ".join(parts)


def normalize_telugu_bible_reference(text: str) -> str:
    text = normalize_spoken_numbers(text)
    tokens = tokenize(text)
    classified = classify(tokens)
    return parse(classified)


class TeluguNormalizer:
    def normalize(self, text: str) -> str:
        return normalize_telugu_bible_reference(text)
