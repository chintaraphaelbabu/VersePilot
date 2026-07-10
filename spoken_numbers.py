from __future__ import annotations

import re

ENGLISH_NUMBER_WORDS = {
    "zero": 0,
    "oh": 0,
    "one": 1,
    "first": 1,
    "two": 2,
    "second": 2,
    "three": 3,
    "third": 3,
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

TELUGU_ONESE = {
    "ఒకటి": 1, "ఒకటవ": 1, "ఒకటో": 1, "మొదటి": 1, "మొదటో": 1,
    "రెండు": 2, "రెండవ": 2, "రెండో": 2,
    "మూడు": 3, "మూడవ": 3, "మూడో": 3,
    "నాలుగు": 4, "నాలుగవ": 4, "నాలుగో": 4, "నాల్గవ": 4,
    "ఐదు": 5, "ఐదవ": 5, "ఐదో": 5, "అయిదు": 5, "అయిదవ": 5, "అయిదో": 5,
    "ఆరు": 6, "ఆరవ": 6, "ఆరో": 6,
    "ఏడు": 7, "ఏడవ": 7, "ఏడో": 7,
    "ఎనిమిది": 8, "ఎనిమిదవ": 8, "ఎనిమిదో": 8,
    "తొమ్మిది": 9, "తొమ్మిదవ": 9, "తొమ్మిదో": 9
}

TELUGU_TEENS = {
    "పదకొండు": 11,
    "పన్నెండు": 12,
    "పదమూడు": 13,
    "పద్నాలుగు": 14,
    "పదిహేను": 15, "పదహేను": 15,
    "పదహారు": 16,
    "పదిహేడు": 17, "పదహేడు": 17,
    "పద్దెనిమిది": 18,
    "పంతొమ్మిది": 19
}

TELUGU_TENS = {
    "పది": 10, "పదవ": 10, "పదో": 10,
    "ఇరవై": 20, "ఇరవది": 20,
    "ముప్పై": 30, "ముప్పది": 30,
    "నలభై": 40, "నలభది": 40,
    "యాభై": 50, "యాభది": 50, "యాబై": 50,
    "అరవై": 60, "అరవది": 60,
    "డెబ్బై": 70, "డెబ్బది": 70, "డెబై": 70,
    "ఎనభై": 80, "ఎనభది": 80, "ఎనబై": 80,
    "తొంభై": 90, "తొంభది": 90, "తొంబై": 90
}

TELUGU_HUNDREDS = {
    "వంద": 100, "నూట": 100, "నూరు": 100
}

TOKEN_PATTERN = re.compile(r"[\w\u0C00-\u0C7F]+|[:\-]")


def _consume_english_number(tokens: list[str], start: int) -> tuple[int | None, int]:
    first = ENGLISH_NUMBER_WORDS.get(tokens[start])
    if first is None:
        return None, 0

    if first < 10:
        next_index = start + 1
        if next_index < len(tokens):
            next_value = ENGLISH_NUMBER_WORDS.get(tokens[next_index])
            if next_value is not None and next_value < 10:
                return None, 0
        return first, 1

    total = first
    consumed = 1

    index = start + 1
    while index < len(tokens):
        token = tokens[index]
        if token == "and":
            consumed += 1
            index += 1
            continue

        value = ENGLISH_NUMBER_WORDS.get(token)
        if value is None:
            break

        if value < 10:
            total += value
        elif value == 100:
            total = max(total, 1) * 100
        elif value == 1000:
            total = max(total, 1) * 1000
        else:
            total += value

        consumed += 1
        index += 1

    return total, consumed


def _consume_telugu_number(tokens: list[str], start: int) -> tuple[int | None, int]:
    index = start
    val = 0
    consumed = 0

    # 1. Hundreds
    if index < len(tokens) and tokens[index] in TELUGU_HUNDREDS:
        val += TELUGU_HUNDREDS[tokens[index]]
        index += 1
        consumed += 1

    # 2. Teens, Tens, or Ones
    if index < len(tokens):
        t = tokens[index]
        if t in TELUGU_TEENS:
            val += TELUGU_TEENS[t]
            index += 1
            consumed += 1
        elif t in TELUGU_TENS:
            val += TELUGU_TENS[t]
            index += 1
            consumed += 1
            if index < len(tokens) and tokens[index] in TELUGU_ONESE:
                val += TELUGU_ONESE[tokens[index]]
                index += 1
                consumed += 1
        elif t in TELUGU_ONESE:
            val += TELUGU_ONESE[t]
            index += 1
            consumed += 1

    if consumed > 0:
        return val, consumed
    return None, 0


def normalize_spoken_numbers(text: str) -> str:
    lowered = text.lower().replace("-", " ")
    tokens = TOKEN_PATTERN.findall(lowered)

    result: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.isdigit():
            result.append(token)
            index += 1
            continue

        # Try consuming as Telugu number
        val_te, consumed_te = _consume_telugu_number(tokens, index)
        if consumed_te:
            result.append(str(val_te))
            index += consumed_te
            continue

        # Try consuming as English number
        value, consumed = _consume_english_number(tokens, index)
        if consumed:
            result.append(str(value))
            index += consumed
            continue

        result.append(token)
        index += 1

    return re.sub(r"\s+", " ", " ".join(result)).strip()