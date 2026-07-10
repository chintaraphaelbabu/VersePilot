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

TELUGU_NUMBER_WORDS = {
    "సున్నా": 0,
    "ఒకటి": 1,
    "మొదటి": 1,
    "రెండు": 2,
    "రెండవ": 2,
    "మూడు": 3,
    "మూడవ": 3,
    "నాలుగు": 4,
    "ఐదు": 5,
    "ఆరు": 6,
    "ఏడు": 7,
    "ఎనిమిది": 8,
    "తొమ్మిది": 9,
    "పది": 10,
    "పదకొండు": 11,
    "పన్నెండు": 12,
    "పదమూడు": 13,
    "పద్నాలుగు": 14,
    "పదిహేను": 15,
    "పదహారు": 16,
    "పదిహేడు": 17,
    "పద్దెనిమిది": 18,
    "పంతొమ్మిది": 19,
    "ఇరవై": 20,
    "ముప్పై": 30,
    "నలభై": 40,
    "యాభై": 50,
    "అరవై": 60,
    "డెబ్బై": 70,
    "ఎనభై": 80,
    "తొంభై": 90,
    "వంద": 100,
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


def _replace_telugu_number_tokens(tokens: list[str]) -> list[str]:
    converted: list[str] = []
    for token in tokens:
        value = TELUGU_NUMBER_WORDS.get(token)
        converted.append(str(value) if value is not None else token)
    return converted


def normalize_spoken_numbers(text: str) -> str:
    lowered = text.lower().replace("-", " ")
    tokens = TOKEN_PATTERN.findall(lowered)
    tokens = _replace_telugu_number_tokens(tokens)

    result: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.isdigit():
            result.append(token)
            index += 1
            continue

        value, consumed = _consume_english_number(tokens, index)
        if consumed:
            result.append(str(value))
            index += consumed
            continue

        result.append(token)
        index += 1

    return re.sub(r"\s+", " ", " ".join(result)).strip()