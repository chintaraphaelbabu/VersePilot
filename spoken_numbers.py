from __future__ import annotations

import re


def _add_word(d: dict[str, int], base: str, val: int) -> None:
    stem = base[:-1] if base[-1] in "ుి" else base
    d[base] = val
    d[stem + "వ"] = val
    d[stem + "ో"] = val
    d[stem + "వది"] = val
    d[stem + "ోది"] = val


def _add_cardinal(d: dict[str, int], base: str, val: int) -> None:
    """Add cardinal forms only (no ordinal generation)."""
    d[base] = val


NUMBER_WORDS: dict[str, int] = {}

# -- Telugu units 1-9 ---------------------------------------------------
_add_word(NUMBER_WORDS, "రెండు", 2)
_add_word(NUMBER_WORDS, "మూడు", 3)
_add_word(NUMBER_WORDS, "నాలుగు", 4)
_add_word(NUMBER_WORDS, "ఐదు", 5)
_add_word(NUMBER_WORDS, "అయిదు", 5)
_add_word(NUMBER_WORDS, "ఆరు", 6)
_add_word(NUMBER_WORDS, "ఏడు", 7)
_add_word(NUMBER_WORDS, "ఎనిమిది", 8)
_add_word(NUMBER_WORDS, "తొమ్మిది", 9)
# Specials for 1
NUMBER_WORDS.update({
    "ఒకటి": 1, "ఒకటవ": 1, "ఒకటో": 1, "ఒకటవది": 1, "ఒకటోది": 1,
    "మొదటి": 1, "మొదట": 1, "మొదటో": 1, "మొదటిది": 1,
})
# Short form for 4
NUMBER_WORDS.update({
    "నాల్గు": 4, "నాల్గవ": 4, "నాల్గో": 4, "నాల్గవది": 4, "నాల్గోది": 4,
})

# -- Telugu teens 11-19 -------------------------------------------------
_add_word(NUMBER_WORDS, "పదకొండు", 11)
_add_word(NUMBER_WORDS, "పన్నెండు", 12)
_add_word(NUMBER_WORDS, "పదమూడు", 13)
_add_word(NUMBER_WORDS, "పద్నాలుగు", 14)
_add_word(NUMBER_WORDS, "పదిహేను", 15)
_add_word(NUMBER_WORDS, "పదహేను", 15)
_add_word(NUMBER_WORDS, "పదహారు", 16)
_add_word(NUMBER_WORDS, "పదిహేడు", 17)
_add_word(NUMBER_WORDS, "పదహేడు", 17)
_add_word(NUMBER_WORDS, "పద్దెనిమిది", 18)
_add_word(NUMBER_WORDS, "పంతొమ్మిది", 19)

# -- Telugu tens 10, 20-90 ----------------------------------------------
_add_word(NUMBER_WORDS, "పది", 10)
# Tens ending in "ై": cardinal only (ordinals use "య్య" infix, handled below)
_add_cardinal(NUMBER_WORDS, "ఇరవై", 20)
_add_cardinal(NUMBER_WORDS, "ముప్పై", 30)
_add_cardinal(NUMBER_WORDS, "నలభై", 40)
_add_cardinal(NUMBER_WORDS, "యాభై", 50)
_add_cardinal(NUMBER_WORDS, "అరవై", 60)
_add_cardinal(NUMBER_WORDS, "డెబ్బై", 70)
_add_cardinal(NUMBER_WORDS, "ఎనభై", 80)
_add_cardinal(NUMBER_WORDS, "తొంభై", 90)
# Alternative tens forms
_add_word(NUMBER_WORDS, "ఇరవది", 20)
_add_word(NUMBER_WORDS, "ముప్పది", 30)
_add_word(NUMBER_WORDS, "నలభది", 40)
_add_word(NUMBER_WORDS, "యాభది", 50)
_add_cardinal(NUMBER_WORDS, "యాబై", 50)
_add_word(NUMBER_WORDS, "అరవది", 60)
_add_word(NUMBER_WORDS, "డెబ్బది", 70)
_add_cardinal(NUMBER_WORDS, "డెబై", 70)
_add_word(NUMBER_WORDS, "ఎనభది", 80)
_add_cardinal(NUMBER_WORDS, "ఎనబై", 80)
_add_word(NUMBER_WORDS, "తొంభది", 90)
_add_cardinal(NUMBER_WORDS, "తొంబై", 90)
# Ordinals for tens ending in "ై" (use "య్య" infix)
def _add_ten_ordinals(stem: str, val: int) -> None:
    NUMBER_WORDS[stem + "వ"] = val
    NUMBER_WORDS[stem + "ో"] = val
    NUMBER_WORDS[stem + "వది"] = val
    NUMBER_WORDS[stem + "ోది"] = val
_add_ten_ordinals("ఇరవయ్య", 20)
_add_ten_ordinals("ముప్పయ్య", 30)
_add_ten_ordinals("నలభయ్య", 40)
_add_ten_ordinals("యాభయ్య", 50)
_add_ten_ordinals("అరవయ్య", 60)
_add_ten_ordinals("డెబ్బయ్య", 70)
_add_ten_ordinals("ఎనభయ్య", 80)
_add_ten_ordinals("తొంభయ్య", 90)

# -- Telugu hundred -----------------------------------------------------
_add_word(NUMBER_WORDS, "వంద", 100)
_add_word(NUMBER_WORDS, "నూరు", 100)
_add_cardinal(NUMBER_WORDS, "నూట", 100)

# -- English number words -----------------------------------------------
ENGLISH_WORDS: dict[str, int] = {
    "zero": 0, "oh": 0,
    "one": 1, "first": 1,
    "two": 2, "second": 2,
    "three": 3, "third": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
    "thousand": 1000,
}
NUMBER_WORDS.update(ENGLISH_WORDS)

# -- Patterns -----------------------------------------------------------
TOKEN_PATTERN = re.compile(r"[\w\u0C00-\u0C7F]+|[:\-]")
DIGIT_ORD_PATTERN = re.compile(r"^(\d+)(వది|ోది|వ|ో)$")


def _consume(tokens: list[str], start: int) -> tuple[int | None, int]:
    if start >= len(tokens):
        return None, 0

    token = tokens[start]
    val = NUMBER_WORDS.get(token)

    if val is None:
        m = DIGIT_ORD_PATTERN.match(token)
        if m:
            return int(m.group(1)), 1
        return None, 0

    # Only compose at most 2-word compounds for these patterns:
    # 1. tens (20-90) + unit (1-9) → additive (20+3=23)
    # 2. unit (1-9) + hundred/thousand → multiplicative (1*100=100)
    # 3. hundred + tens (20-90) → additive (100+20=120)

    if start + 1 < len(tokens):
        next_t = tokens[start + 1]
        next_v = NUMBER_WORDS.get(next_t)

        if next_v is not None:
            if 20 <= val <= 90 and 1 <= next_v <= 9:
                return val + next_v, 2
            if 1 <= val <= 9 and next_v == 100:
                return val * 100, 2
            if 1 <= val <= 9 and next_v == 1000:
                return val * 1000, 2
            if val == 100 and 20 <= next_v <= 90:
                return val + next_v, 2

    return val, 1


def normalize_spoken_numbers(text: str) -> str:
    lowered = text.lower().replace("-", " ")
    tokens = TOKEN_PATTERN.findall(lowered)

    result: list[str] = []
    i = 0
    while i < len(tokens):
        if tokens[i].isdigit():
            result.append(tokens[i])
            i += 1
            continue

        val, n = _consume(tokens, i)
        if n:
            result.append(str(val))
            i += n
            continue

        result.append(tokens[i])
        i += 1

    return re.sub(r"\s+", " ", " ".join(result)).strip()
