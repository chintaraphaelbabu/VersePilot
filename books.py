from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BookEntry:
    canonical: str
    aliases: tuple[str, ...]


BOOKS: tuple[BookEntry, ...] = (
    BookEntry("Genesis", ("genesis", "ఆదికాండము", "ఆదికాండం")),
    BookEntry("Exodus", ("exodus", "నిర్గమకాండము", "నిర్గమకాండం")),
    BookEntry("Leviticus", ("leviticus", "లేవీయకాండము")),
    BookEntry("Numbers", ("numbers", "సంఖ్యాకాండము")),
    BookEntry("Deuteronomy", ("deuteronomy", "ద్వితీయోపదేశకాండము")),
    BookEntry("Joshua", ("joshua", "యెహోషువ")),
    BookEntry("Judges", ("judges", "న్యాయాధిపతులు")),
    BookEntry("Ruth", ("ruth", "రూతు")),
    BookEntry("1 Samuel", ("1 samuel", "first samuel", "1 సమూయేలు", "మొదటి సమూయేలు")),
    BookEntry("2 Samuel", ("2 samuel", "second samuel", "2 సమూయేలు", "రెండవ సమూయేలు")),
    BookEntry("1 Kings", ("1 kings", "first kings", "1 రాజులు")),
    BookEntry("2 Kings", ("2 kings", "second kings", "2 రాజులు")),
    BookEntry("1 Chronicles", ("1 chronicles", "first chronicles", "1 దినవృత్తాంతములు")),
    BookEntry("2 Chronicles", ("2 chronicles", "second chronicles", "2 దినవృత్తాంతములు")),
    BookEntry("Ezra", ("ezra", "ఎజ్రా")),
    BookEntry("Nehemiah", ("nehemiah", "నెహెమ్యా")),
    BookEntry("Esther", ("esther", "ఎస్తేరు")),
    BookEntry("Job", ("job", "యోబు")),
    BookEntry("Psalms", ("psalms", "psalm", "కీర్తనలు")),
    BookEntry("Proverbs", ("proverbs", "సామెతలు")),
    BookEntry("Ecclesiastes", ("ecclesiastes", "ప్రసంగి")),
    BookEntry("Song of Solomon", ("song of solomon", "song of songs", "పరమగీతము")),
    BookEntry("Isaiah", ("isaiah", "యెషయా")),
    BookEntry("Jeremiah", ("jeremiah", "యిర్మియా")),
    BookEntry("Lamentations", ("lamentations", "విలాపవాక్యములు")),
    BookEntry("Ezekiel", ("ezekiel", "యెహెజ్కేలు")),
    BookEntry("Daniel", ("daniel", "దానియేలు")),
    BookEntry("Hosea", ("hosea", "హోషేయా")),
    BookEntry("Joel", ("joel", "యోవేలు")),
    BookEntry("Amos", ("amos", "ఆమోసు")),
    BookEntry("Obadiah", ("obadiah", "ఓబద్యా")),
    BookEntry("Jonah", ("jonah", "యోనా")),
    BookEntry("Micah", ("micah", "మీకా")),
    BookEntry("Nahum", ("nahum", "నహూము")),
    BookEntry("Habakkuk", ("habakkuk", "హబక్కూకు")),
    BookEntry("Zephaniah", ("zephaniah", "జెఫన్యా")),
    BookEntry("Haggai", ("haggai", "హగ్గయి")),
    BookEntry("Zechariah", ("zechariah", "జెకర్యా")),
    BookEntry("Malachi", ("malachi", "మలాకీ")),
    BookEntry("Matthew", ("matthew", "మత్తయి")),
    BookEntry("Mark", ("mark", "మార్కు")),
    BookEntry("Luke", ("luke", "లూకా")),
    BookEntry("John", ("john", "యోహాను")),
    BookEntry("Acts", ("acts", "అపొస్తలుల కార్యములు")),
    BookEntry("Romans", ("romans", "రోమీయులకు")),
    BookEntry("1 Corinthians", ("1 corinthians", "first corinthians", "1 కొరింథీయులకు")),
    BookEntry("2 Corinthians", ("2 corinthians", "second corinthians", "2 కొరింథీయులకు")),
    BookEntry("Galatians", ("galatians", "గలతీయులకు")),
    BookEntry("Ephesians", ("ephesians", "ఎఫెసీయులకు")),
    BookEntry("Philippians", ("philippians", "ఫిలిప్పీయులకు")),
    BookEntry("Colossians", ("colossians", "కొలొస్సయులకు")),
    BookEntry("1 Thessalonians", ("1 thessalonians", "first thessalonians", "1 థెస్సలొనీకయులకు")),
    BookEntry("2 Thessalonians", ("2 thessalonians", "second thessalonians", "2 థెస్సలొనీకయులకు")),
    BookEntry("1 Timothy", ("1 timothy", "first timothy", "1 తిమోతికి")),
    BookEntry("2 Timothy", ("2 timothy", "second timothy", "2 తిమోతికి")),
    BookEntry("Titus", ("titus", "తీతుకు")),
    BookEntry("Philemon", ("philemon", "ఫిలేమోనుకు")),
    BookEntry("Hebrews", ("hebrews", "హెబ్రీయులకు")),
    BookEntry("James", ("james", "యాకోబు")),
    BookEntry("1 Peter", ("1 peter", "first peter", "1 పేతురు")),
    BookEntry("2 Peter", ("2 peter", "second peter", "2 పేతురు")),
    BookEntry("1 John", ("1 john", "first john", "1 యోహాను")),
    BookEntry("2 John", ("2 john", "second john", "2 యోహాను")),
    BookEntry("3 John", ("3 john", "third john", "3 యోహాను")),
    BookEntry("Jude", ("jude", "యూదా")),
    BookEntry("Revelation", ("revelation", "ప్రకటన", "ప్రకటన గ్రంథము")),
)


def whisper_vocabulary_terms() -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()

    for entry in BOOKS:
        for term in (entry.canonical, *entry.aliases):
            normalized = term.strip()
            if not normalized:
                continue

            key = normalized.casefold()
            if key in seen:
                continue

            seen.add(key)
            terms.append(normalized)

    for term in ("chapter", "verse", "verses"):
        key = term.casefold()
        if key not in seen:
            seen.add(key)
            terms.append(term)

    return terms


def whisper_initial_prompt() -> str:
    terms = whisper_vocabulary_terms()
    return (
        "This audio contains Bible references in English and Telugu. "
        "Use this vocabulary: " + ", ".join(terms) + "."
    )