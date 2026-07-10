from __future__ import annotations
import re
from typing import Any, NamedTuple

class Token(NamedTuple):
    type: str  # 'BOOK', 'NUMBER', 'CHAPTER_MARKER', 'VERSE_MARKER', 'CORRECTION', 'IGNORE', 'UNKNOWN'
    text: str
    value: Any = None

# Data-driven configuration of Bible book aliases
BOOK_ALIASES: dict[str, list[str]] = {
    "Genesis": ["genesis", "ఆదికాండము", "ఆదికాండం", "ఆదికాండము గ్రంథము", "ఆదికాండము గ్రంథం", "ఆదికాండము పుస్తకము", "ఆదికాండము పుస్తకం"],
    "Exodus": ["exodus", "నిర్గమకాండము", "నిర్గమకాండం", "నిర్గమకాండము గ్రంథము", "నిర్గమకాండము గ్రంథం", "నిర్గమకాండము పుస్తకము", "నిర్గమకాండము పుస్తకం"],
    "Leviticus": ["leviticus", "లేవీయకాండము", "లేవీయకాండం", "లేవీయకాండము గ్రంథము", "లేవీయకాండము గ్రంథం", "లేవీయకాండము పుస్తకము", "లేవీయకాండము పుస్తకం"],
    "Numbers": ["numbers", "సంఖ్యాకాండము", "సంఖ్యాకాండం", "సంఖ్యాకాండము గ్రంథము", "సంఖ్యాకాండము గ్రంథం", "సంఖ్యాకాండము పుస్తకము", "సంఖ్యాకాండము పుస్తకం"],
    "Deuteronomy": ["deuteronomy", "ద్వితీయోపదేశకాండము", "ద్వితీయోపదేశకాండం", "ద్వితీయోపదేశకాండము గ్రంథము", "ద్వితీయోపదేశకాండము పుస్తకము", "ద్వితీయోపదేశకాండము పుస్తకం"],
    "Joshua": ["joshua", "యెహోషువ", "యెహోషువ గ్రంథము", "యెహోషువ పుస్తకం", "యెహోషువకు"],
    "Judges": ["judges", "న్యాయాధిపతులు", "న్యాయాధిపతుల గ్రంథము", "న్యాయాధిపతుల పుస్తకం"],
    "Ruth": ["ruth", "రూతు", "రూతు గ్రంథము", "రూతు పుస్తకం", "రూతుకు"],
    "1 Samuel": ["1 samuel", "first samuel", "మొదటి సమూయేలు", "1 సమూయేలు", "మొదటి సమూయేలు గ్రంథము", "మొదటి సమూయేలు పుస్తకం", "1 సమూయేలు గ్రంథము", "1 సమూయేలు పుస్తకం"],
    "2 Samuel": ["2 samuel", "second samuel", "రెండవ సమూయేలు", "2 సమూయేలు", "రెండవ సమూయేలు గ్రంథము", "రెండవ సమూయేలు పుస్తకం", "2 సమూయేలు గ్రంథము", "2 సమూయేలు పుస్తకం"],
    "1 Kings": ["1 kings", "first kings", "మొదటి రాజులు", "1 రాజులు", "మొదటి రాజుల గ్రంథము", "మొదటి రాజుల పుస్తకం", "1 రాజుల గ్రంథము", "1 రాజుల పుస్తకం"],
    "2 Kings": ["2 kings", "second kings", "రెండవ రాజులు", "2 రాజులు", "రెండవ రాజుల గ్రంథము", "రెండవ రాజుల పుస్తకం", "2 రాజుల గ్రంథము", "2 రాజుల పుస్తకం"],
    "1 Chronicles": ["1 chronicles", "first chronicles", "మొదటి దినవృత్తాంతములు", "1 దినవృత్తాంతములు", "మొదటి దినవృత్తాంతముల గ్రంథము", "మొదటి దినవృత్తాంతముల పుస్తకం", "1 దినవృత్తాంతముల గ్రంథము", "1 దినవృత్తాంతముల పుస్తకం"],
    "2 Chronicles": ["2 chronicles", "second chronicles", "రెండవ దినవృత్తాంతములు", "2 దినవృత్తాంతములు", "రెండవ దినవృత్తాంతముల గ్రంథము", "రెండవ దినవృత్తాంతముల పుస్తకం", "2 దినవృత్తాంతముల గ్రంథము", "2 దినవృత్తాంతముల పుస్తకం"],
    "Ezra": ["ezra", "ఎజ్రా", "ఎజ్రా గ్రంథము", "ఎజ్రా పుస్తకం", "ఎజ్రాకు"],
    "Nehemiah": ["nehemiah", "నెహెమ్యా", "నెహెమ్యా గ్రంథము", "నెహెమ్యా పుస్తకం", "నెహెమ్యాకు"],
    "Esther": ["esther", "ఎస్తేరు", "ఎస్తేరు గ్రంథము", "ఎస్తేరు పుస్తకం", "ఎస్తేరుకు"],
    "Job": ["job", "యోబు", "యోబు గ్రంథము", "యోబు పుస్తకం", "యోబుకు"],
    "Psalms": ["psalms", "psalm", "కీర్తనలు", "కీర్తన", "కీర్తనల గ్రంథము", "కీర్తనల పుస్తకం"],
    "Proverbs": ["proverbs", "సామెతలు", "సామెతల గ్రంథము", "సామెతల పుస్తకం"],
    "Ecclesiastes": ["ecclesiastes", "ప్రసంగి", "ప్రసంగి గ్రంథము", "ప్రసంగి పుస్తకం"],
    "Song of Solomon": ["song of solomon", "song of songs", "పరమగీతము", "పరమగీతం", "పరమగీతములు"],
    "Isaiah": ["isaiah", "యెషయా", "యెషయా గ్రంథము", "యెషయా పుస్తకం", "యెషయాకు"],
    "Jeremiah": ["jeremiah", "యిర్మియా", "యిర్మియా గ్రంథము", "యిర్మియా పుస్తకం", "యిర్మియాకు"],
    "Lamentations": ["lamentations", "విలాపవాక్యములు", "విలాపవాక్యాలు", "యిర్మియా విలాపవాక్యములు", "యిర్మియా విలాపవాక్యాలు"],
    "Ezekiel": ["ezekiel", "యెహెజ్కేలు", "యెహెజ్కేలు గ్రంథము", "యెహెజ్కేలు పుస్తకం", "యెహెజ్కేలుకు"],
    "Daniel": ["daniel", "దానియేలు", "దానియేలు గ్రంథము", "దానియేలు పుస్తకం", "దానియేలుకు"],
    "Hosea": ["hosea", "హోషేయా", "హోషేయా గ్రంథము", "హోషేయా పుస్తకం", "హోషేయాకు"],
    "Joel": ["joel", "యోవేలు", "యోవేలు గ్రంథము", "యోవేలు పుస్తకం", "యోవేలుకు", "యోవేలుకు వ్రాసిన గ్రంథము", "యోవేలుకు వ్రాసిన పుస్తకం"],
    "Amos": ["amos", "ఆమోసు", "ఆమోసుకు", "ఆమోసుకు వ్రాసిన గ్రంథము", "ఆమోసుకు వ్రాసిన పుస్తకం", "ఆమోసు గ్రంథము", "ఆమోసు పుస్తకం"],
    "Obadiah": ["obadiah", "ఓబద్యా", "ఓబద్యా గ్రంథము", "ఓబద్యా పుస్తకం", "ఓబద్యాకు", "ఓబద్యాకు వ్రాసిన గ్రంథము", "ఓబద్యాకు వ్రాసిన పుస్తకం"],
    "Jonah": ["jonah", "యోనా", "యోనా గ్రంథము", "యోనా పుస్తకం", "యోనాకు", "యోనాకు వ్రాసిన గ్రంథము", "యోనాకు వ్రాసిన పుస్తకం"],
    "Micah": ["micah", "మీకా", "మీకా గ్రంథము", "మీకా పుస్తకం", "మీకాకు", "మీకాకు వ్రాసిన గ్రంథము", "మీకాకు వ్రాసిన పుస్తకం"],
    "Nahum": ["nahum", "నహూము", "నహూము గ్రంథము", "నహూము పుస్తకం", "నహూముకు", "నహూముకు వ్రాసిన గ్రంథము", "నహూముకు వ్రాసిన పుస్తకం"],
    "Habakkuk": ["habakkuk", "హబక్కూకు", "హబక్కూకు గ్రంథము", "హబక్కూకు పుస్తకం", "హబక్కూకుకు", "హబక్కూకుకు వ్రాసిన గ్రంథము", "హబక్కూకుకు వ్రాసిన పుస్తకం"],
    "Zephaniah": ["zephaniah", "జెఫన్యా", "జెఫన్యా గ్రంథము", "జెఫన్యా పుస్తకం", "జెఫన్యాకు", "జెఫన్యాకు వ్రాసిన గ్రంథము", "జెఫన్యాకు వ్రాసిన పుస్తకం"],
    "Haggai": ["haggai", "హగ్గయి", "హగ్గయి గ్రంథము", "హగ్గయి పుస్తకం", "హగ్గయికి", "హగ్గయికి వ్రాసిన గ్రంథము", "హగ్గయికి వ్రాసిన పుస్తకం"],
    "Zechariah": ["zechariah", "జెకర్యా", "జెకర్యా గ్రంథము", "జెకర్యా పుస్తకం", "జెకర్యాకు", "జెకర్యాకు వ్రాసిన గ్రంథము", "జెకర్యాకు వ్రాసిన పుస్తకం"],
    "Malachi": ["malachi", "మలాకీ", "మలాకీ గ్రంథము", "మలాకీ పుస్తకం", "మలాకీకి", "మలాకీకి వ్రాసిన గ్రంథము", "మలాకీకి వ్రాసిన పుస్తకం"],
    "Matthew": ["matthew", "మత్తయి", "మత్తయి సువార్త", "మత్తయి వ్రాసిన సువార్త", "మత్తయికు"],
    "Mark": ["mark", "మార్కు", "మార్కు సువార్త", "మార్కు వ్రాసిన సువార్త", "మార్కుకు"],
    "Luke": ["luke", "లూకా", "లూకా సువార్త", "లూకా వ్రాసిన సువార్త", "లూకాకు"],
    "John": ["john", "యోహాను", "యోహాను సువార్త", "యోహాను వ్రాసిన సువార్త", "యోహానుకు"],
    "Acts": ["acts", "అపొస్తలుల కార్యములు", "అపొస్తలుల కార్యాలు"],
    "Romans": ["romans", "రోమీయులకు", "రోమీయులకు వ్రాసిన పత్రిక", "రోమీయుల పత్రిక"],
    "1 Corinthians": ["1 corinthians", "1 కొరింథీయులకు", "మొదటి కొరింథీయులకు", "మొదటి కొరింథీయులకు వ్రాసిన పత్రిక", "1 కొరింథీయులకు వ్రాసిన పత్రిక"],
    "2 Corinthians": ["2 corinthians", "2 కొరింథీయులకు", "రెండవ కొరింథీయులకు", "రెండవ కొరింథీయులకు వ్రాసిన పత్రిక", "2 కొరింథీయులకు వ్రాసిన పత్రిక"],
    "Galatians": ["galatians", "గలతీయులకు", "గలతీయులకు వ్రాసిన పత్రిక", "గలతీయుల పత్రిక"],
    "Ephesians": ["ephesians", "ఎఫెసీయులకు", "ఎఫెసీయులకు వ్రాసిన పత్రిక", "ఎఫెసీయుల పత్రిక"],
    "Philippians": ["philippians", "ఫిలిప్పీయులకు", "ఫిలిప్పీయులకు వ్రాసిన పత్రిక", "ఫిలిప్పీయుల పత్రిక"],
    "Colossians": ["colossians", "కొలొస్సయులకు", "కొలొస్సయులకు వ్రాసిన పత్రిక", "కొలొస్సయుల పత్రిక"],
    "1 Thessalonians": ["1 thessalonians", "1 థెస్సలొనీకయులకు", "మొదటి థెస్సలొనీకయులకు", "మొదటి థెస్సలొనీకయులకు వ్రాసిన పత్రిక", "1 థెస్సలొనీకయులకు వ్రాసిన పత్రిక"],
    "2 Thessalonians": ["2 thessalonians", "2 థెస్సలొనీకయులకు", "రెండవ థెస్సలొనీకయులకు", "రెండవ థెస్సలొనీకయులకు వ్రాసిన పత్రిక", "2 థెస్సలొనీకయులకు వ్రాసిన పత్రిక"],
    "1 Timothy": ["1 timothy", "1 తిమోతికి", "మొదటి తిమోతికి", "మొదటి తిమోతికి వ్రాసిన పత్రిక", "1 తిమోతికి వ్రాసిన పత్రిక"],
    "2 Timothy": ["2 timothy", "2 తిమోతికి", "రెండవ తిమోతికి", "రెండవ తిమోతికి వ్రాసిన పత్రిక", "2 తిమోతికి వ్రాసిన పత్రిక"],
    "Titus": ["titus", "తీతుకు", "తీతుకు వ్రాసిన పత్రిక", "తీతు పత్రిక"],
    "Philemon": ["philemon", "ఫిలేమోనుకు", "ఫిలేమోనుకు వ్రాసిన పత్రిక", "ఫిలేమోను పత్రిక"],
    "Hebrews": ["hebrews", "హెబ్రీయులకు", "హెబ్రీయులకు వ్రాసిన పత్రిక", "హెబ్రీయుల పత్రిక"],
    "James": ["james", "యాకోబు", "యాకోబు వ్రాసిన పత్రిక", "యాకోబు పత్రిక", "యాకోబుకు"],
    "1 Peter": ["1 peter", "1 పేతురు", "మొదటి పేతురు", "మొదటి పేతురు వ్రాసిన పత్రిక", "1 పేతురు వ్రాసిన పత్రిక"],
    "2 Peter": ["2 peter", "2 పేతురు", "రెండవ పేతురు", "రెండవ పేతురు వ్రాసిన పత్రిక", "2 పేతురు వ్రాసిన పత్రిక"],
    "1 John": ["1 john", "1 యోహాను", "మొదటి యోహాను", "మొదటి యోహాను వ్రాసిన పత్రిక", "1 యోహాను వ్రాసిన పత్రిక"],
    "2 John": ["2 john", "2 యోహాను", "రెండవ యోహాను", "రెండవ యోహాను వ్రాసిన పత్రిక", "2 యోహాను వ్రాసిన పత్రిక"],
    "3 John": ["3 john", "3 యోహాను", "మూడవ యోహాను", "మూడవ యోహాను వ్రాసిన పత్రిక", "3 యోహాను వ్రాసిన పత్రిక"],
    "Jude": ["jude", "యూదా", "యూదా వ్రాసిన పత్రిక", "యూదా పత్రిక", "యూదాకు"],
    "Revelation": ["revelation", "ప్రకటన", "ప్రకటన గ్రంథము", "ప్రకటన గ్రంథం", "యోహాను ప్రకటన గ్రంథము"]
}

# Number words mapped directly to digits
NUMBER_WORDS: dict[str, int] = {
    # Telugu
    "సున్నా": 0,
    "ఒకటి": 1, "మొదటి": 1, "ఒకటో": 1, "ఒకటవ": 1, "మొదటో": 1,
    "రెండు": 2, "రెండవ": 2, "రెండో": 2,
    "మూడు": 3, "మూడవ": 3, "మూడో": 3,
    "నాలుగు": 4, "నాలుగవ": 4, "నాల్గవ": 4, "నాలుగో": 4, "నాల్గో": 4,
    "ఐదు": 5, "ఐదవ": 5, "ఐదో": 5,
    "ఆరు": 6, "ఆరవ": 6, "ఆరో": 6,
    "ఏడు": 7, "ఏడవ": 7, "ఏడో": 7,
    "ఎనిమిది": 8, "ఎనిమిదవ": 8, "ఎనిమిదో": 8,
    "తొమ్మిది": 9, "తొమ్మిదవ": 9, "తొమ్మిదో": 9,
    "పది": 10, "పదవ": 10, "పదో": 10,
    "పదకొండు": 11, "పదకొండో": 11, "పదకొండవ": 11,
    "పన్నెండు": 12, "పన్నెండో": 12, "పన్నెండవ": 12,
    "పదమూడు": 13, "పదమూడో": 13, "పదమూడవ": 13,
    "పద్నాలుగు": 14, "పద్నాలుగో": 14, "పద్నాలుగవ": 14,
    "పదిహేను": 15, "పదిహేనో": 15, "పదిహేనవ": 15,
    "పదహారు": 16, "పదహారో": 16, "పదహారవ": 16,
    "పదిహేడు": 17, "పదిహేడో": 17, "పదిహేడవ": 17,
    "పద్దెనిమిది": 18, "పద్దెనిమిదో": 18, "పద్దెనిమిదవ": 18,
    "పంతొమ్మిది": 19, "పంతొమ్మిదో": 19, "పంతొమ్మిదవ": 19,
    "ఇరవై": 20, "ముప్పై": 30, "నలభై": 40, "యాభై": 50, "అరవై": 60, "డెబ్బై": 70, "ఎనభై": 80, "తొంభై": 90, "వంద": 100,
    # English
    "zero": 0, "oh": 0, "one": 1, "first": 1, "two": 2, "second": 2, "three": 3, "third": 3,
    "four": 4, "fourth": 4, "five": 5, "fifth": 5, "six": 6, "sixth": 6, "seven": 7, "seventh": 7,
    "eight": 8, "eighth": 8, "nine": 9, "ninth": 9, "ten": 10, "tenth": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
}

CORRECTION_WORDS = {"కాదు", "సారీ", "no", "sorry", "ఆ"}
CHAPTER_WORDS = {"అధ్యాయం", "అధ్యాయము", "chapter", "chapters", "ch"}
VERSE_WORDS = {"వచనం", "వచనము", "వచనాలు", "verse", "verses", "v"}
IGNORE_WORDS = {
    "వ్రాసిన", "గ్రంథము", "గ్రంథం", "పుస్తకము", "పుస్తకం", "పత్రిక", "సువార్త",
    "మనము", "ఇప్పుడు", "చూద్దాం", "తిరగండి", "కొంచెం", "ఒక్కసారి", "దయచేసి", "వెళ్దాం", "అంటే"
}

def tokenize_and_preprocess(text: str) -> list[str]:
    """Splits string into raw tokens and normalizes them."""
    # Match words (English/Telugu) and punctuation like colon/hyphen
    pattern = re.compile(r"[\w\u0C00-\u0C7F]+|[:\-]")
    raw_tokens = pattern.findall(text)
    # Strip whitespace and lowercase English tokens
    return [t.strip().lower() if any(c.isalpha() for c in t) else t.strip() for t in raw_tokens if t.strip()]

def build_sorted_alias_token_lists() -> list[tuple[list[str], str]]:
    """Builds a sorted list of ([alias_tokens], canonical_name), longest first."""
    pairs = []
    for canonical, aliases in BOOK_ALIASES.items():
        all_aliases = set(aliases + [canonical])
        for alias in all_aliases:
            if alias:
                tokens = tokenize_and_preprocess(alias)
                if tokens:
                    pairs.append((tokens, canonical))
    pairs.sort(key=lambda x: (len(x[0]), len(" ".join(x[0]))), reverse=True)
    return pairs

SORTED_ALIAS_TOKENS = build_sorted_alias_token_lists()

def match_book_tokens(tokens: list[str], start_idx: int) -> tuple[str | None, int]:
    """Tries to match sequential tokens starting at start_idx to a book alias."""
    for alias_toks, canonical in SORTED_ALIAS_TOKENS:
        length = len(alias_toks)
        if start_idx + length <= len(tokens):
            subsegment = tokens[start_idx : start_idx + length]
            match = True
            for a_tok, s_tok in zip(alias_toks, subsegment):
                s_tok_clean = s_tok
                for suffix in ["కు", "కి", "నకు", "ల"]:
                    if s_tok.endswith(suffix) and len(s_tok) > len(suffix) + 1:
                        s_tok_clean = s_tok[:-len(suffix)]
                        break
                
                a_tok_clean = a_tok
                for suffix in ["కు", "కి", "నకు", "ల"]:
                    if a_tok.endswith(suffix) and len(a_tok) > len(suffix) + 1:
                        a_tok_clean = a_tok[:-len(suffix)]
                        break

                if a_tok != s_tok and a_tok_clean != s_tok_clean:
                    match = False
                    break
            if match:
                return canonical, length
    return None, 0

def classify_tokens(raw_tokens: list[str]) -> list[Token]:
    """Classifies a list of raw string tokens into typed Token objects."""
    classified: list[Token] = []
    i = 0
    while i < len(raw_tokens):
        book_canonical, length = match_book_tokens(raw_tokens, i)
        if book_canonical:
            matched_text = " ".join(raw_tokens[i : i + length])
            classified.append(Token("BOOK", matched_text, book_canonical))
            i += length
            continue

        token_str = raw_tokens[i]
        
        if token_str in CORRECTION_WORDS:
            classified.append(Token("CORRECTION", token_str))
            i += 1
            continue

        if token_str in CHAPTER_WORDS:
            classified.append(Token("CHAPTER_MARKER", token_str))
            i += 1
            continue

        if token_str in VERSE_WORDS:
            classified.append(Token("VERSE_MARKER", token_str))
            i += 1
            continue

        if token_str in IGNORE_WORDS:
            classified.append(Token("IGNORE", token_str))
            i += 1
            continue

        digit_match = re.match(r"^(\d+)", token_str)
        if digit_match:
            val = int(digit_match.group(1))
            classified.append(Token("NUMBER", token_str, val))
            i += 1
            continue

        if token_str in NUMBER_WORDS:
            classified.append(Token("NUMBER", token_str, NUMBER_WORDS[token_str]))
            i += 1
            continue

        cleaned_tok = token_str
        for suffix in ["వ", "వో", "వది", "వము", "వది", "వ"]:
            if token_str.endswith(suffix) and len(token_str) > len(suffix):
                cleaned_tok = token_str[:-len(suffix)]
                if cleaned_tok in NUMBER_WORDS:
                    classified.append(Token("NUMBER", token_str, NUMBER_WORDS[cleaned_tok]))
                    break
        else:
            classified.append(Token("UNKNOWN", token_str))
            
        i += 1

    return classified

def parse_tokens(tokens: list[Token]) -> str:
    """Parses typed tokens using a stack-based state machine to handle context/corrections."""
    history = [(None, None, None, None)]
    
    expecting_chapter = False
    expecting_verse = False
    last_type = None

    for tok in tokens:
        if tok.type in ("IGNORE", "UNKNOWN"):
            continue
            
        current_book, current_chapter, current_verse, current_end_verse = history[-1]
        
        if tok.type == "BOOK":
            history.append((tok.value, None, None, None))
            expecting_chapter = False
            expecting_verse = False

        elif tok.type == "NUMBER":
            val = tok.value
            if expecting_verse:
                history.append((current_book, current_chapter, val, None))
                expecting_verse = False
            elif expecting_chapter:
                history.append((current_book, val, current_verse, None))
                expecting_chapter = False
            else:
                if current_chapter is None:
                    history.append((current_book, val, current_verse, None))
                elif current_verse is None:
                    history.append((current_book, current_chapter, val, None))
                else:
                    history.append((current_book, current_chapter, current_verse, val))

        elif tok.type == "CHAPTER_MARKER":
            if current_verse is not None and len(history) > 1:
                last_num = current_verse
                history.pop()
                prev_b, prev_c, prev_v, prev_ev = history[-1]
                history.append((prev_b, last_num, None, None))
            elif last_type == "NUMBER":
                expecting_chapter = False
                expecting_verse = False
            else:
                expecting_chapter = True
                expecting_verse = False

        elif tok.type == "VERSE_MARKER":
            if last_type == "NUMBER":
                expecting_chapter = False
                expecting_verse = False
            else:
                expecting_verse = True
                expecting_chapter = False

        elif tok.type == "CORRECTION":
            if len(history) > 1:
                history.pop()
            expecting_chapter = False
            expecting_verse = False

        last_type = tok.type

    final_book, final_chapter, final_verse, final_end_verse = history[-1]
    
    parts = []
    if final_book:
        parts.append(final_book)
    if final_chapter is not None:
        parts.append(str(final_chapter))
    if final_verse is not None:
        parts.append(str(final_verse))
    if final_end_verse is not None:
        parts.append(str(final_end_verse))
        
    if not parts:
        nums = [str(tok.value) for tok in tokens if tok.type == "NUMBER"]
        return " ".join(nums)

    return " ".join(parts)

def normalize_telugu_bible_reference(text: str) -> str:
    """Tokenizes and parses Telugu sermon text into a simplified reference string."""
    raw_tokens = tokenize_and_preprocess(text)
    classified = classify_tokens(raw_tokens)
    return parse_tokens(classified)

class TeluguNormalizer:
    def __init__(self) -> None:
        pass

    def normalize(self, text: str) -> str:
        return normalize_telugu_bible_reference(text)
