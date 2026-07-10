from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BookEntry:
    canonical: str
    aliases: tuple[str, ...]


BOOKS: tuple[BookEntry, ...] = (
    BookEntry("Genesis", ("genesis", "gen", "ge", "ఆదికాండము", "ఆదికాండం", "ఆది", "ఆదికాండము గ్రంథము")),
    BookEntry("Exodus", ("exodus", "ex", "exo", "నిర్గమకాండము", "నిర్గమకాండం", "నిర్గమ", "నిర్గమకాండము గ్రంథము")),
    BookEntry("Leviticus", ("leviticus", "lev", "lv", "లేవీయకాండము", "లేవీయకాండం", "లేవీయ", "లేవీయకాండము గ్రంథము")),
    BookEntry("Numbers", ("numbers", "num", "nm", "సంఖ్యాకాండము", "సంఖ్యాకాండం", "సంఖ్యా", "సంఖ్యాకాండము గ్రంథము")),
    BookEntry("Deuteronomy", ("deuteronomy", "deut", "dt", "ద్వితీయోపదేశకాండము", "ద్వితీయోపదేశకాండం", "ద్వితీయో", "ద్వితీయోపదేశకాండము గ్రంథము")),
    BookEntry("Joshua", ("joshua", "josh", "jos", "యెహోషువ", "యెహోషువ గ్రంథం", "యెహో", "యెహోషువ గ్రంథము")),
    BookEntry("Judges", ("judges", "judg", "jdg", "న్యాయాధిపతులు", "న్యాయాధిపతుల గ్రంథం", "న్యాయాధిపతుల గ్రంథము", "న్యాయా", "న్యాయaధిపతులు")),
    BookEntry("Ruth", ("ruth", "rut", "ru", "రూతు", "రూతు గ్రంథం", "రూతు గ్రంథము")),
    BookEntry("1 Samuel", ("1 samuel", "1 sam", "1sm", "first samuel", "1 సమూయేలు", "మొదటి సమూయేలు", "1 సమూయేలు గ్రంథం", "మొదటి సమూయేలు గ్రంథము")),
    BookEntry("2 Samuel", ("2 samuel", "2 sam", "2sm", "second samuel", "2 సమూయేలు", "రెండవ సమూయేలు", "2 సమూయేలు గ్రంథం", "రెండవ సమూయేలు గ్రంథము")),
    BookEntry("1 Kings", ("1 kings", "1 kgs", "1ki", "first kings", "1 రాజులు", "మొదటి రాజులు", "1 రాజుల గ్రంథం", "మొదటి రాజుల గ్రంథము")),
    BookEntry("2 Kings", ("2 kings", "2 kgs", "2ki", "second kings", "2 రాజులు", "రెండవ రాజులు", "2 రాజుల గ్రంథం", "రెండవ రాజుల గ్రంథము")),
    BookEntry("1 Chronicles", ("1 chronicles", "1 chron", "1 chr", "1ch", "first chronicles", "1 దినవృత్తాంతములు", "మొదటి దినవృత్తాంతములు", "1 దినవృత్తాంతాలు", "మొదటి దినవృత్తాంతాలు")),
    BookEntry("2 Chronicles", ("2 chronicles", "2 chron", "2 chr", "2ch", "second chronicles", "2 దినవృత్తాంతములు", "రెండవ దినవృత్తాంతములు", "2 దినవృత్తాంతాలు", "రెండవ దినవృత్తాంతాలు")),
    BookEntry("Ezra", ("ezra", "ezr", "ఎజ్రా", "ఎజ్రా గ్రంథం", "ఎజ్రా గ్రంథము")),
    BookEntry("Nehemiah", ("nehemiah", "neh", "ne", "నెహెమ్యా", "నెహెమ్యా గ్రంథం", "నెహెమ్యా గ్రంథము")),
    BookEntry("Esther", ("esther", "esth", "est", "es", "ఎస్తేరు", "ఎస్తేరు గ్రంథం", "ఎస్తేరు గ్రంథము")),
    BookEntry("Job", ("job", "jb", "యోబు", "యోబు గ్రంథం", "యోబు గ్రంథము")),
    BookEntry("Psalms", ("psalms", "psalm", "ps", "కీర్తనలు", "కీర్తన", "కీర్త", "క్రం", "కీర్తనల గ్రంథము", "కీర్తనల గ్రంథం")),
    BookEntry("Proverbs", ("proverbs", "prov", "pro", "pr", "సామెతలు", "సామెత", "సామెతల గ్రంథము", "సామెతల గ్రంథం")),
    BookEntry("Ecclesiastes", ("ecclesiastes", "eccl", "ecc", "ec", "ప్రసంగి", "ప్రసంగి గ్రంథము", "ప్రసంగి గ్రంథం")),
    BookEntry("Song of Solomon", ("song of solomon", "song of songs", "song", "songs", "sos", "పరమగీతము", "పరమగీతం", "పరమ గీతము")),
    BookEntry("Isaiah", ("isaiah", "isa", "is", "యెషయా", "యెషయా గ్రంథం", "యెషయా గ్రంథము")),
    BookEntry("Jeremiah", ("jeremiah", "jer", "je", "యిర్మియా", "యిర్మియా గ్రంథం", "యిర్మియా గ్రంథము")),
    BookEntry("Lamentations", ("lamentations", "lam", "la", "విలాపవాక్యములు", "విలాపవాక్యాలు", "యిర్మియా విలాపవాక్యములు")),
    BookEntry("Ezekiel", ("ezekiel", "ezek", "eze", "ez", "యెహెజ్కేలు", "యెహెజ్కేలు గ్రంథం", "యెహెజ్కేలు గ్రంథము", "యెహెజ్కేల్")),
    BookEntry("Daniel", ("daniel", "dan", "dn", "దానియేలు", "దానియేలు గ్రంథం", "దానియేలు గ్రంథము", "దాని")),
    BookEntry("Hosea", ("hosea", "hos", "హోషేయా", "హోషేయా గ్రంథం", "హోషేయా గ్రంథము")),
    BookEntry("Joel", ("joel", "joe", "jl", "యోవేలు", "యోవేలు గ్రంథం", "యోవేలు గ్రంథము")),
    BookEntry("Amos", ("amos", "amo", "am", "ఆమోసు", "ఆమోసు గ్రంథం", "ఆమోసు గ్రంథము")),
    BookEntry("Obadiah", ("obadiah", "obad", "ob", "ఓబద్యా", "ఓబద్యా గ్రంథం", "ఓబద్యా గ్రంథము")),
    BookEntry("Jonah", ("jonah", "jon", "యోనా", "యోనా గ్రంథం", "యోనా గ్రంథము")),
    BookEntry("Micah", ("micah", "mic", "మీకా", "మీకా గ్రంథం", "మీకా గ్రంథము")),
    BookEntry("Nahum", ("nahum", "nah", "na", "నహూము", "నహూము గ్రంథం", "నహూము గ్రంథము")),
    BookEntry("Habakkuk", ("habakkuk", "hab", "హబక్కూకు", "హబక్కూకు గ్రంథం", "హబక్కూకు గ్రంథము")),
    BookEntry("Zephaniah", ("zephaniah", "zeph", "zep", "zp", "జెఫన్యా", "జెఫన్యా గ్రంథం", "జెఫన్యా గ్రంథము")),
    BookEntry("Haggai", ("haggai", "hag", "హగ్గయి", "హగ్గయి గ్రంథం", "హగ్గయి గ్రంథము")),
    BookEntry("Zechariah", ("zechariah", "zech", "zec", "zc", "జెకర్యా", "జెకర్యా గ్రంథం", "జెకర్యా గ్రంథము")),
    BookEntry("Malachi", ("malachi", "mal", "ml", "మలాకీ", "మలాకీ గ్రంథం", "మలాకీ గ్రంథము")),
    BookEntry("Matthew", ("matthew", "matt", "mat", "mt", "మత్తయి", "మత్తయి సువార్త", "మత్త")),
    BookEntry("Mark", ("mark", "mrk", "mk", "మార్కు", "మార్కు సువార్త")),
    BookEntry("Luke", ("luke", "luk", "lk", "లూకా", "లూకా సువార్త")),
    BookEntry("John", ("john", "joh", "jn", "యోహాను", "యోహాను సువార్త", "యోహ", "యోహను", "యోహానూ", "యోహాన")),
    BookEntry("Acts", ("acts", "act", "ac", "అపొస్తలుల కార్యములు", "అపొస్తలుల కార్యాలు", "అపొస్తలుల")),
    BookEntry("Romans", ("romans", "rom", "ro", "rm", "రోమీయులకు", "రోమీయులకు వ్రాసిన పత్రిక", "రోమీ", "రోమీయులుకు", "రోమియులకు")),
    BookEntry("1 Corinthians", ("1 corinthians", "1 cor", "1co", "first corinthians", "1 కొరింథీయులకు", "మొదటి కొరింథీయులకు", "1 కొరింథీ")),
    BookEntry("2 Corinthians", ("2 corinthians", "2 cor", "2co", "second corinthians", "2 కొరింథీయులకు", "రెండవ కొరింథీయులకు", "2 కొరింథీ")),
    BookEntry("Galatians", ("galatians", "gal", "ga", "గలతీయులకు", "గలతీయులకు వ్రాసిన పత్రిక", "గలతీ")),
    BookEntry("Ephesians", ("ephesians", "eph", "ep", "ఎఫెసీయులకు", "ఎఫెసీయులకు వ్రాసిన పత్రిక", "ఎఫెసీ")),
    BookEntry("Philippians", ("philippians", "phil", "php", "ఫిలిప్పీయులకు", "ఫిలిప్పీయులకు వ్రాసిన పత్రిక", "ఫిలిప్పీ", "ఫిలిప్పి")),
    BookEntry("Colossians", ("colossians", "col", "cl", "కొలొస్సయులకు", "కొలొస్సయులకు వ్రాసిన పత్రిక", "కొలొస్స")),
    BookEntry("1 Thessalonians", ("1 thessalonians", "1 thess", "1th", "first thessalonians", "1 థెస్సలొనీకయులకు", "మొదటి థెస్సలొనీకయులకు", "1 థెస్సలొనీక")),
    BookEntry("2 Thessalonians", ("2 thessalonians", "2 thess", "2th", "second thessalonians", "2 థెస్సలొనీకయులకు", "రెండవ థెస్సలొనీకయులకు", "2 థెస్సలొనీక")),
    BookEntry("1 Timothy", ("1 timothy", "1 tim", "1ti", "first timothy", "1 తిమోతికి", "మొదటి తిమోతికి", "1 తిమోతి")),
    BookEntry("2 Timothy", ("2 timothy", "2 tim", "2ti", "second timothy", "2 తిమోతికి", "రెండవ తిమోతికి", "2 తిమోతి")),
    BookEntry("Titus", ("titus", "tit", "ti", "తీతుకు", "తీతు", "తీతు పత్రిక")),
    BookEntry("Philemon", ("philemon", "philem", "phm", "pm", "ఫిలేమోనుకు", "ఫిలేమోను", "ఫిలేమోను పత్రిక")),
    BookEntry("Hebrews", ("hebrews", "heb", "he", "హెబ్రీయులకు", "హెబ్రీయులకు వ్రాసిన పత్రిక", "హెబ్రీ")),
    BookEntry("James", ("james", "jas", "jm", "యాకోబు", "యాకోబు పత్రిక")),
    BookEntry("1 Peter", ("1 peter", "1 pet", "1pe", "first peter", "1 పేతురు", "మొదటి పేతురు", "1 పేతురు పత్రిక")),
    BookEntry("2 Peter", ("2 peter", "2 pet", "2pe", "second peter", "2 పేతురు", "రెండవ పేతురు", "2 పేతురు పత్రిక")),
    BookEntry("1 John", ("1 john", "1 jn", "1jo", "first john", "1 యోహాను", "మొదటి యోహాను", "1 యోహాను పత్రిక")),
    BookEntry("2 John", ("2 john", "2 jn", "2jo", "second john", "2 యోహాను", "రెండవ యోహాను", "2 యోహాను పత్రిక")),
    BookEntry("3 John", ("3 john", "3 jn", "3jo", "third john", "3 యోహాను", "మూడవ యోహాను", "3 యోహాను పత్రిక")),
    BookEntry("Jude", ("jude", "jud", "jd", "యూదా", "యూదా పత్రిక")),
    BookEntry("Revelation", ("revelation", "rev", "re", "ప్రకటన", "ప్రకటన గ్రంథము", "ప్రకటన గ్రంధము", "ప్రక", "యోహాను ప్రకటన")),
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

    extra_words = (
        "chapter", "verse", "verses", "book", "scripture",
        "అధ్యాయం", "వచనం", "వచనము", "గ్రంథము", "సువార్త"
    )
    for term in extra_words:
        key = term.casefold()
        if key not in seen:
            seen.add(key)
            terms.append(term)

    return terms


def whisper_initial_prompt() -> str:
    terms = whisper_vocabulary_terms()
    return (
        "This audio contains Bible references spoken in Telugu, English, and mixed language. "
        "Use this vocabulary: " + ", ".join(terms) + "."
    )