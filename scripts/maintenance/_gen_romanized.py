"""Generate Romanized Telugu book aliases and write them to a file (no Telugu output to terminal)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

# Transliteration mapping for Telugu book names to Roman script
# This covers the common STT Romanization patterns

CONSONANT_MAP = {
    "\u0c15": "k",    # క
    "\u0c16": "kh",   # ఖ
    "\u0c17": "g",    # గ
    "\u0c18": "gh",   # ఘ
    "\u0c19": "ng",   # ఙ
    "\u0c1a": "ch",   # చ
    "\u0c1b": "chh",  # ఛ
    "\u0c1c": "j",    # జ
    "\u0c1d": "jh",   # ఝ
    "\u0c1e": "ny",   # ఞ
    "\u0c1f": "t",    # ట
    "\u0c20": "th",   # ఠ
    "\u0c21": "d",    # డ
    "\u0c22": "dh",   # ఢ
    "\u0c23": "n",    # ణ
    "\u0c24": "t",    # త
    "\u0c25": "th",   # థ
    "\u0c26": "d",    # ద
    "\u0c27": "dh",   # ధ
    "\u0c28": "n",    # న
    "\u0c2a": "p",    # ప
    "\u0c2b": "ph",   # ఫ
    "\u0c2c": "b",    # బ
    "\u0c2d": "bh",   # భ
    "\u0c2e": "m",    # మ
    "\u0c2f": "y",    # య
    "\u0c30": "r",    # ర
    "\u0c32": "l",    # ల
    "\u0c33": "l",    # ళ
    "\u0c35": "v",    # వ
    "\u0c36": "sh",   # శ
    "\u0c37": "sh",   # ష
    "\u0c38": "s",    # స
    "\u0c39": "h",    # హ
}

VOWEL_MAP = {
    "\u0c05": "a",    # అ
    "\u0c06": "aa",   # ఆ
    "\u0c07": "i",    # ఇ
    "\u0c08": "ee",   # ఈ
    "\u0c09": "u",    # ఉ
    "\u0c0a": "oo",   # ఊ
    "\u0c0b": "ru",   # ఋ
    "\u0c0e": "e",    # ఎ
    "\u0c0f": "e",    # ఏ
    "\u0c10": "ai",   # ఐ
    "\u0c12": "o",    # ఒ
    "\u0c13": "o",    # ఓ
    "\u0c14": "au",   # ఔ
}

VOWEL_SIGNS = {
    "\u0c3e": "aa",   # ా
    "\u0c3f": "i",    # ి
    "\u0c40": "ee",   # ీ
    "\u0c41": "u",    # ు
    "\u0c42": "oo",   # ూ
    "\u0c43": "ru",   # ృ
    "\u0c46": "e",    # ె
    "\u0c47": "e",    # ే
    "\u0c48": "ai",   # ై
    "\u0c4a": "o",    # ొ
    "\u0c4b": "o",    # ో
    "\u0c4c": "au",   # ౌ
}


def telugu_to_roman(word: str) -> str:
    """Transliterate a Telugu word to Roman script."""
    result = []
    i = 0
    while i < len(word):
        ch = word[i]

        # Compound: క్ష
        if i + 2 < len(word) and word[i : i + 3] == "\u0c15\u0c4d\u0c37":
            result.append("ksh")
            i += 3
            continue

        # Halant (removes inherent vowel)
        if ch == "\u0c4d":
            i += 1
            continue

        # Special: Anusvara (ం) - nasalizes next consonant
        if ch == "\u0c02":
            result.append("m")
            i += 1
            continue

        # Visarga (ః)
        if ch == "\u0c03":
            result.append("h")
            i += 1
            continue

        # Vowel signs (dependent diacritics)
        if ch in VOWEL_SIGNS:
            result.append(VOWEL_SIGNS[ch])
            i += 1
            continue

        # Independent vowel at start or after another vowel
        if ch in VOWEL_MAP:
            result.append(VOWEL_MAP[ch])
            i += 1
            continue

        # Consonants
        if ch in CONSONANT_MAP:
            base = CONSONANT_MAP[ch]
            # Peek at next char
            if i + 1 < len(word):
                next_ch = word[i + 1]
                if next_ch == "\u0c4d":
                    # Halant follows: no vowel
                    result.append(base)
                    i += 2
                elif next_ch in VOWEL_SIGNS:
                    # Vowel sign follows: add consonant without inherent vowel
                    result.append(base)
                    i += 1
                else:
                    # No vowel sign: add inherent 'a'
                    result.append(base + "a")
                    i += 1
            else:
                # Last char: add inherent 'a' unless ending with 'ు' or 'ూ'
                if word[-1:] in ("\u0c41", "\u0c42"):
                    result.append(base)
                else:
                    result.append(base + "a")
                i += 1
            continue

        # Other (shouldn't happen with valid Telugu)
        i += 1

    return "".join(result)


def generate_variants(roman: str) -> set[str]:
    """Generate common phonetic variants of a Romanized word."""
    variants = {roman}
    lowered = roman.lower()

    # Drop trailing 'a' (common STT simplification)
    if lowered.endswith("a") and len(lowered) > 2:
        variants.add(lowered[:-1])

    # 'aa' → 'a' simplification (STT sometimes drops length)
    if "aa" in lowered:
        variants.add(lowered.replace("aa", "a"))

    # 'ee' → 'i' simplification
    if "ee" in lowered:
        variants.add(lowered.replace("ee", "i"))

    # 'oo' → 'u' simplification
    if "oo" in lowered:
        variants.add(lowered.replace("oo", "u"))

    # 'sh' → 's' simplification
    if "sh" in lowered:
        variants.add(lowered.replace("sh", "s"))

    # 'ph' → 'p' simplification
    if "ph" in lowered:
        variants.add(lowered.replace("ph", "p"))

    # 'ch' → 's' for some words (like yochana → yosana)
    if "ch" in lowered:
        variants.add(lowered.replace("ch", "s"))

    # Remove 'h' after consonants (bh → b, dh → d, etc.)
    for pair in ["bh", "dh", "gh", "kh", "ph", "th", "chh"]:
        if pair in lowered:
            variants.add(lowered.replace(pair, pair[0]))

    # 'ksh' → 'ks'
    if "ksh" in lowered:
        variants.add(lowered.replace("ksh", "ks"))

    return {v for v in variants if len(v) >= 2}


def main():
    # Import book entries
    sys.path.insert(0, ".")
    from versepilot.books import BOOKS

    lines = []
    for entry in BOOKS:
        canon = entry.canonical
        for alias in entry.telugu_aliases:
            roman = telugu_to_roman(alias)
            variants = generate_variants(roman)
            for var in sorted(variants, key=lambda x: -len(x)):
                if len(var) >= 2:
                    lines.append(f'    ("{var}", "{canon}"),  # from {alias}')

    # Also generate from spoken_variants
    for entry in BOOKS:
        canon = entry.canonical
        for alias in entry.spoken_variants:
            if any("\u0c00" <= c <= "\u0c7f" for c in alias):  # Telugu script
                roman = telugu_to_roman(alias)
                if roman not in ("", alias.lower()):
                    lines.append(f'    ("{roman}", "{canon}"),  # from {alias}')
                # Also short forms
                short = roman.replace("akaandamu", "").replace("akandamu", "").replace("aandamu", "").strip()
                if short and len(short) >= 2 and short != roman:
                    lines.append(f'    ("{short}", "{canon}"),  # short from {alias}')

    out_path = "C:\\Users\\Raphael\\Documents\\verses\\_romanized_output.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("ROMANIZED_LOOKUP: dict[str, str] = {\n")
        for line in sorted(set(lines)):
            f.write(line + "\n")
        f.write("}\n")
    print(f"Written to {out_path}")


if __name__ == "__main__":
    main()
