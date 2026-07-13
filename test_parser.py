from __future__ import annotations

from normalizer import normalize_telugu_bible_reference
from parser import BibleReferenceParser
from intent_detector import IntentDetector

parser = BibleReferenceParser()
detector = IntentDetector()

# (input, expected_normalizer_output, expected_parser_canonical_or_None)
NORMALIZER_TESTS: list[tuple[str, str, str | None]] = []


def _t(inp: str, norm: str, canon: str | None = None) -> None:
    NORMALIZER_TESTS.append((inp, norm, canon))


# ===== 1. English references =====
_t("John 3 16", "John 3 16", "John 3:16")
_t("John 3:16", "John 3 16", "John 3:16")
_t("Genesis 1 1", "Genesis 1 1", "Genesis 1:1")
_t("Matthew 5 3", "Matthew 5 3", "Matthew 5:3")
_t("Psalm 23", "Psalms 23", "Psalms 23")
_t("Psalms 23 1", "Psalms 23 1", "Psalms 23:1")
_t("Proverbs 3 5", "Proverbs 3 5", "Proverbs 3:5")
_t("Exodus 20 1 17", "Exodus 20 1 17", "Exodus 20:1-17")
_t("Romans 8 28", "Romans 8 28", "Romans 8:28")
_t("Revelation 22 21", "Revelation 22 21", "Revelation 22:21")
_t("Acts 2 38", "Acts 2 38", "Acts 2:38")
_t("Hebrews 11 1", "Hebrews 11 1", "Hebrews 11:1")
_t("Genesis 1 26 28", "Genesis 1 26 28", "Genesis 1:26-28")
_t("Matthew 28 19 20", "Matthew 28 19 20", "Matthew 28:19-20")
_t("Psalm 119 105", "Psalms 119 105", "Psalms 119:105")

# English with chapter/verse markers
_t("John chapter 3 verse 16", "John 3 16", "John 3:16")
_t("Genesis chapter 1 verse 1", "Genesis 1 1", "Genesis 1:1")
_t("Romans chapter 8", "Romans 8", "Romans 8")
_t("Matthew chapter 5 verse 3", "Matthew 5 3", "Matthew 5:3")
_t("Psalm chapter 23 verse 1", "Psalms 23 1", "Psalms 23:1")

# English with number words
_t("first John 3 16", "1 John 3 16", "1 John 3:16")
_t("second Corinthians 5 17", "2 Corinthians 5 17", "2 Corinthians 5:17")
_t("first Timothy 3 16", "1 Timothy 3 16", "1 Timothy 3:16")
_t("second Timothy 3 16", "2 Timothy 3 16", "2 Timothy 3:16")
_t("first Peter 3 15", "1 Peter 3 15", "1 Peter 3:15")
_t("second Peter 1 4", "2 Peter 1 4", "2 Peter 1:4")
_t("third John 1", "3 John 1", "3 John 1")

# English book-only
_t("Psalms", "Psalms", None)
_t("Genesis", "Genesis", None)
_t("Romans", "Romans", None)
_t("Revelation", "Revelation", None)

# English chapter-only
_t("Genesis 1", "Genesis 1", "Genesis 1")
_t("John 3", "John 3", "John 3")
_t("Psalms 23", "Psalms 23", "Psalms 23")
_t("Romans 8", "Romans 8", "Romans 8")

# ===== 2. Telugu references =====
_t("ఆమోసు మూడు నాలుగు", "Amos 3 4", "Amos 3:4")
_t("ఆమోసు మూడు నాల్గవ వచనం", "Amos 3 4", "Amos 3:4")
_t("మత్తయి మూడు పదహారు", "Matthew 3 16", "Matthew 3:16")
_t("మత్తయి మూడవ అధ్యాయం పదహారవ వచనం", "Matthew 3 16", "Matthew 3:16")
_t("యోహాను మూడు పదహారు", "John 3 16", "John 3:16")
_t("యోహాను మూడవ అధ్యాయము పదహారవ వచనము", "John 3 16", "John 3:16")
_t("ఆదికాండము ఒకటి ఒకటి", "Genesis 1 1", "Genesis 1:1")
_t("కీర్తనలు ఇరవై మూడు", "Psalms 23", "Psalms 23")
_t("కీర్తనలు ఇరవై మూడు ఒకటి", "Psalms 23 1", "Psalms 23:1")
_t("రోమీయులకు ఎనిమిది ఇరవై ఎనిమిది", "Romans 8 28", "Romans 8:28")
_t("ప్రకటన ఇరవై రెండు ఇరవై ఒకటి", "Revelation 22 21", "Revelation 22:21")
_t("అపొస్తలుల కార్యములు రెండు ముప్పై ఎనిమిది", "Acts 2 38", "Acts 2:38")
_t("హెబ్రీయులకు పదకొండు ఒకటి", "Hebrews 11 1", "Hebrews 11:1")

# Telugu with digit ordinals
_t("రోమీయులకు 12వ అధ్యాయము 2వ వచనము", "Romans 12 2", "Romans 12:2")
_t("మత్తయి 3వ అధ్యాయం 16వ వచనం", "Matthew 3 16", "Matthew 3:16")
_t("కీర్తనలు 23వ అధ్యాయము 1వ వచనము", "Psalms 23 1", "Psalms 23:1")
_t("యోహాను 3వ అధ్యాయము 16వ వచనము", "John 3 16", "John 3:16")

# Telugu book-only
_t("ఆమోసు", "Amos", None)
_t("మత్తయి", "Matthew", None)
_t("రోమీయులకు", "Romans", None)
_t("కీర్తనలు", "Psalms", None)
_t("ప్రకటన", "Revelation", None)

# Telugu chapter-only
_t("ఆమోసు మూడు", "Amos 3", "Amos 3")
_t("మత్తయి మూడు", "Matthew 3", "Matthew 3")
_t("కీర్తనలు ఇరవై మూడు", "Psalms 23", "Psalms 23")
_t("యోహాను మూడు", "John 3", "John 3")

# Telugu verse-only (no book)
_t("వచనం నాలుగు", "4", None)
_t("పదహారు", "16", None)

# ===== 3. Mixed Telugu-English =====
_t("Romans ఎనిమిది 28", "Romans 8 28", "Romans 8:28")
_t("John మూడు పదహారు", "John 3 16", "John 3:16")
_t("Matthew అయిదు మూడు", "Matthew 5 3", "Matthew 5:3")
_t("Psalms ఇరవై మూడు ఒకటి", "Psalms 23 1", "Psalms 23:1")
_t("Acts రెండు ముప్పై ఎనిమిది", "Acts 2 38", "Acts 2:38")
_t("Revelation ఇరవై రెండు ఇరవై ఒకటి", "Revelation 22 21", "Revelation 22:21")
_t("యోహాను 3 16", "John 3 16", "John 3:16")
_t("Romans 8 28", "Romans 8 28", "Romans 8:28")
_t("మత్తయి 5 3", "Matthew 5 3", "Matthew 5:3")
_t("కీర్తనలు 23 1", "Psalms 23 1", "Psalms 23:1")
_t("Genesis ఒకటి 1", "Genesis 1 1", "Genesis 1:1")
_t("Romans chapter ఎనిమిది verse ఇరవై ఎనిమిది", "Romans 8 28", "Romans 8:28")
_t("Matthew chapter అయిదు verse మూడు", "Matthew 5 3", "Matthew 5:3")
_t("John మూడు chapter పదహారు", "John 3 16", "John 3:16")

# ===== 4. Corrections =====
_t("ఆమోసు మూడవ అధ్యాయం కాదు నాలుగవ అధ్యాయం", "Amos 4", "Amos 4")
_t("మత్తయి సువార్త 3 అధ్యాయం సారీ 4 అధ్యాయం 16 వచనం", "Matthew 4 16", "Matthew 4:16")
_t("Genesis 13 sorry 16 4", "Genesis 16 4", "Genesis 16:4")
_t("John 3 no 4 16", "John 4 16", "John 4:16")
_t("Romans 8 no 9 28", "Romans 9 28", "Romans 9:28")
_t("ఆమోసు మూడు కాదు నాలుగు", "Amos 4", "Amos 4")
_t("మత్తయి మూడు సారీ నాలుగు", "Matthew 4", "Matthew 4")
_t("ఆమోసుకు కాదు యోనా", "Jonah", None)
_t("Romans 8 28 కాదు 8 29", "Romans 8 29", "Romans 8:29")
_t("యోహాను 3 16 సారీ 3 17", "John 3 17", "John 3:17")
_t("John 3 15 sorry 16", "John 3 16", "John 3:16")
_t("ఆమోసు 3 4 ఆ 3 5", "Amos 3 5", "Amos 3:5")

# ===== 5. Cross references =====
_t("see also John 3 16", "John 3 16", "John 3:16")
_t("compare Romans 8 28", "Romans 8 28", "Romans 8:28")
_t("చూడండి మత్తయి 5 3", "Matthew 5 3", "Matthew 5:3")
_t("cross reference Genesis 1 1", "Genesis 1 1", "Genesis 1:1")
_t("look at Psalms 23", "Psalms 23", "Psalms 23")
_t("see also John 3", "John 3", "John 3")
_t("పోల్చి రోమీయులకు 8 28", "Romans 8 28", "Romans 8:28")

# ===== 6. Navigation =====
# Navigation commands should NOT produce a reference, normalizer returns empty
def nav(inp: str) -> None:
    _t(inp, "", None)

nav("next verse")
nav("previous verse")
nav("next chapter")
nav("previous chapter")
nav("go back")
nav("go back to passage")
nav("continue")
nav("continue reading")
nav("return to the passage")
_t("verse 5", "5", None)
_t("chapter 3", "3", None)
nav("తరువాతి వచనం")
nav("తరువాతి అధ్యాయం")
nav("next వచనం")
nav("previous వచనం")
nav("ముందటి వచనం")
nav("ముందటి అధ్యాయం")
nav("next అధ్యాయం")
nav("prev verse")
nav("prev chapter")

# ===== 7. Pastor speech / Non-Bible =====
def non_bible(inp: str) -> None:
    _t(inp, "", None)

non_bible("let us pray")
non_bible("good morning everyone")
non_bible("amen")
non_bible("hallelujah")
non_bible("please turn to your neighbor")
non_bible("let us stand")
non_bible("thank you")
non_bible("praise the Lord")
non_bible("we will now read")
non_bible("please be seated")
non_bible("close your eyes")
non_bible("ఆమెను")
non_bible("మన ప్రార్థన")
non_bible("thank you Jesus")
non_bible("నమస్కారము")

# ===== 8. Numbered books =====
_t("1 Timothy 3 16", "1 Timothy 3 16", "1 Timothy 3:16")
_t("2 Timothy 3 16", "2 Timothy 3 16", "2 Timothy 3:16")
_t("1 Corinthians 13", "1 Corinthians 13", "1 Corinthians 13")
_t("2 Corinthians 5 17", "2 Corinthians 5 17", "2 Corinthians 5:17")
_t("1 Kings 18", "1 Kings 18", "1 Kings 18")
_t("2 Kings 2", "2 Kings 2", "2 Kings 2")
_t("1 Samuel 3", "1 Samuel 3", "1 Samuel 3")
_t("2 Samuel 3", "2 Samuel 3", "2 Samuel 3")
_t("1 Chronicles 1", "1 Chronicles 1", "1 Chronicles 1")
_t("2 Chronicles 1", "2 Chronicles 1", "2 Chronicles 1")
_t("1 Peter 3 15", "1 Peter 3 15", "1 Peter 3:15")
_t("2 Peter 1 4", "2 Peter 1 4", "2 Peter 1:4")
_t("1 John 1", "1 John 1", "1 John 1")
_t("2 John 1", "2 John 1", "2 John 1")
_t("3 John 1", "3 John 1", "3 John 1")
_t("1 Thessalonians 5", "1 Thessalonians 5", "1 Thessalonians 5")
_t("2 Thessalonians 3", "2 Thessalonians 3", "2 Thessalonians 3")

# Numbered books with spoken number words
_t("first Timothy 3 16", "1 Timothy 3 16", "1 Timothy 3:16")
_t("second Timothy 3 16", "2 Timothy 3 16", "2 Timothy 3:16")
_t("first Corinthians 13", "1 Corinthians 13", "1 Corinthians 13")
_t("second Corinthians 5 17", "2 Corinthians 5 17", "2 Corinthians 5:17")
_t("third John 1", "3 John 1", "3 John 1")

# Numbered books with base names
_t("Timothy 3 16", "1 Timothy 3 16", "1 Timothy 3:16")
_t("Corinthians 13", "1 Corinthians 13", "1 Corinthians 13")
_t("Samuel 3", "1 Samuel 3", "1 Samuel 3")
_t("Peter 3 15", "1 Peter 3 15", "1 Peter 3:15")
_t("John 1", "John 1", "John 1")  # Gospel, not epistle

# Numbered books with number prefix
_t("1 సమూయేలు 3", "1 Samuel 3", "1 Samuel 3")
_t("2 సమూయేలు 3", "2 Samuel 3", "2 Samuel 3")
_t("1 కొరింథీయులకు 13", "1 Corinthians 13", "1 Corinthians 13")
_t("2 కొరింథీయులకు 5 17", "2 Corinthians 5 17", "2 Corinthians 5:17")
_t("1 తిమోతికి 3 16", "1 Timothy 3 16", "1 Timothy 3:16")
_t("2 తిమోతికి 3 16", "2 Timothy 3 16", "2 Timothy 3:16")
_t("1 పేతురు 3 15", "1 Peter 3 15", "1 Peter 3:15")
_t("2 పేతురు 1 4", "2 Peter 1 4", "2 Peter 1:4")
_t("1 యోహాను 1", "1 John 1", "1 John 1")
_t("2 యోహాను 1", "2 John 1", "2 John 1")
_t("3 యోహాను 1", "3 John 1", "3 John 1")

# Numbered books with Telugu number words
_t("మొదటి తిమోతికి 3 16", "1 Timothy 3 16", "1 Timothy 3:16")
_t("రెండవ తిమోతికి 3 16", "2 Timothy 3 16", "2 Timothy 3:16")
_t("మొదటి పేతురు 3 15", "1 Peter 3 15", "1 Peter 3:15")
_t("రెండవ పేతురు 1 4", "2 Peter 1 4", "2 Peter 1:4")
_t("మూడవ యోహాను 1", "3 John 1", "3 John 1")

# ===== 9. Filler words =====
_t("ఆమోసుకు వ్రాసిన గ్రంథము మూడవ అధ్యాయం నాల్గవ వచనం", "Amos 3 4", "Amos 3:4")
_t("రోమీయులకు వ్రాసిన పత్రిక 12వ అధ్యాయము 2వ వచనము", "Romans 12 2", "Romans 12:2")
_t("మత్తయి సువార్త మూడవ అధ్యాయం", "Matthew 3", "Matthew 3")
_t("ఆమోసుకు మనము ఇప్పుడు వ్రాసిన గ్రంథము మూడవ కొంచెం అధ్యాయం నాల్గవ దయచేసి వచనం", "Amos 3 4", "Amos 3:4")
_t("యోహాను సువార్త మూడవ అధ్యాయము పదహారవ వచనము", "John 3 16", "John 3:16")
_t("Romans the epistle to the 8 28", "Romans 8 28", "Romans 8:28")
_t("first of John 3 16", "1 John 3 16", "1 John 3:16")
_t("the book of Genesis 1 1", "Genesis 1 1", "Genesis 1:1")
_t("ఆమోసుకు వ్రాసిన గ్రంథము మూడు అధ్యాయం నాలుగు వచనం", "Amos 3 4", "Amos 3:4")
_t("మత్తయి వ్రాసిన సువార్త మూడవ అధ్యాయం పదహారవ వచనం", "Matthew 3 16", "Matthew 3:16")

# ===== 10. Full long-church name forms =====
_t("ఆమోసుకు వ్రాసిన గ్రంథము", "Amos", None)
_t("రోమీయులకు వ్రాసిన పత్రిక", "Romans", None)
_t("మత్తయి సువార్త", "Matthew", None)
_t("మొదటి కొరింథీయులకు వ్రాసిన పత్రిక 13", "1 Corinthians 13", "1 Corinthians 13")
_t("యోహాను సువార్త 3 16", "John 3 16", "John 3:16")
_t("యెషయా గ్రంథము 53 5", "Isaiah 53 5", "Isaiah 53:5")
_t("కీర్తనల గ్రంథము 23 1", "Psalms 23 1", "Psalms 23:1")
_t("ప్రకటన గ్రంథము 22 21", "Revelation 22 21", "Revelation 22:21")

# ===== 11. Edge cases =====
# Verse range with hyphen
_t("John 3 16 18", "John 3 16 18", "John 3:16-18")
_t("John 3:16-18", "John 3 16 18", "John 3:16-18")
_t("Romans 8 28 30", "Romans 8 28 30", "Romans 8:28-30")
_t("Romans 8:28-30", "Romans 8 28 30", "Romans 8:28-30")

# Single-chapter books
_t("Jude 1", "Jude 1", "Jude 1")
_t("Philemon 1", "Philemon 1", "Philemon 1")
_t("Philemon 1 4", "Philemon 1 4", "Philemon 1:4")
_t("Obadiah 1", "Obadiah 1", "Obadiah 1")

# Suffix stripping
_t("ఆమోసుకు", "Amos", None)
_t("రూతుకు", "Ruth", None)
_t("యోబుకు", "Job", None)
_t("యెహోషువకు", "Joshua", None)
_t("దానియేలుకు", "Daniel", None)

# Telugu spoken variants
_t("ఆది 1 1", "Genesis 1 1", "Genesis 1:1")
_t("నిర్గమ 20 1", "Exodus 20 1", "Exodus 20:1")
_t("ద్వితీయ 6 5", "Deuteronomy 6 5", "Deuteronomy 6:5")
_t("కీర్త 23 1", "Psalms 23 1", "Psalms 23:1")
_t("యెహో 1 1", "Joshua 1 1", "Joshua 1:1")
_t("ప్రక 22 21", "Revelation 22 21", "Revelation 22:21")
_t("రోమీ 8 28", "Romans 8 28", "Romans 8:28")
_t("గలతీ 3 1", "Galatians 3 1", "Galatians 3:1")
_t("మత్త 3 16", "Matthew 3 16", "Matthew 3:16")
_t("యోహ 3 16", "John 3 16", "John 3:16")
_t("దాని 3 16", "Daniel 3 16", "Daniel 3:16")

# English abbreviations
_t("Gen 1 1", "Genesis 1 1", "Genesis 1:1")
_t("Ex 20 1", "Exodus 20 1", "Exodus 20:1")
_t("Lev 19 18", "Leviticus 19 18", "Leviticus 19:18")
_t("Num 6 24", "Numbers 6 24", "Numbers 6:24")
_t("Deut 6 5", "Deuteronomy 6 5", "Deuteronomy 6:5")
_t("Josh 1 1", "Joshua 1 1", "Joshua 1:1")
_t("Ps 23 1", "Psalms 23 1", "Psalms 23:1")
_t("Prov 3 5", "Proverbs 3 5", "Proverbs 3:5")
_t("Isa 53 5", "Isaiah 53 5", "Isaiah 53:5")
_t("Jer 29 11", "Jeremiah 29 11", "Jeremiah 29:11")
_t("Matt 5 3", "Matthew 5 3", "Matthew 5:3")
_t("Heb 11 1", "Hebrews 11 1", "Hebrews 11:1")
_t("Rev 22 21", "Revelation 22 21", "Revelation 22:21")

# No book: numbers only
_t("3 16", "3 16", None)
_t("8 28", "8 28", None)
_t("23", "23", None)
_t("1 1", "1 1", None)

# ===== 12. Corrections with context =====
_t("no it is John 3 16", "John 3 16", "John 3:16")
_t("I meant Romans 8 28", "Romans 8 28", "Romans 8:28")
_t("sorry actually Genesis 1 1", "Genesis 1 1", "Genesis 1:1")
_t("no sorry I mean Matthew 5 3", "Matthew 5 3", "Matthew 5:3")

# ===== 13. Various books cross-check =====
_t("Isaiah 53 5", "Isaiah 53 5", "Isaiah 53:5")
_t("Jeremiah 29 11", "Jeremiah 29 11", "Jeremiah 29:11")
_t("Ezekiel 37 1", "Ezekiel 37 1", "Ezekiel 37:1")
_t("Daniel 3 16", "Daniel 3 16", "Daniel 3:16")
_t("Hosea 11 1", "Hosea 11 1", "Hosea 11:1")
_t("Joel 2 28", "Joel 2 28", "Joel 2:28")
_t("Amos 3 4", "Amos 3 4", "Amos 3:4")
_t("Jonah 1 17", "Jonah 1 17", "Jonah 1:17")
_t("Micah 6 8", "Micah 6 8", "Micah 6:8")
_t("Zechariah 9 9", "Zechariah 9 9", "Zechariah 9:9")
_t("Malachi 3 10", "Malachi 3 10", "Malachi 3:10")
_t("Mark 1 1", "Mark 1 1", "Mark 1:1")
_t("Luke 2 1", "Luke 2 1", "Luke 2:1")
_t("Acts 1 8", "Acts 1 8", "Acts 1:8")
_t("Galatians 5 22", "Galatians 5 22", "Galatians 5:22")
_t("Ephesians 2 8", "Ephesians 2 8", "Ephesians 2:8")
_t("Philippians 4 13", "Philippians 4 13", "Philippians 4:13")
_t("Colossians 3 16", "Colossians 3 16", "Colossians 3:16")
_t("Titus 2 11", "Titus 2 11", "Titus 2:11")
_t("Philemon 1 4", "Philemon 1 4", "Philemon 1:4")
_t("James 1 22", "James 1 22", "James 1:22")

# ===== 14. Telugu book aliases =====
_t("ఆదికాండము 1 1", "Genesis 1 1", "Genesis 1:1")
_t("నిర్గమకాండము 20 1", "Exodus 20 1", "Exodus 20:1")
_t("లేవీయకాండము 19 18", "Leviticus 19 18", "Leviticus 19:18")
_t("సంఖ్యాకాండము 6 24", "Numbers 6 24", "Numbers 6:24")
_t("ద్వితీయోపదేశకాండము 6 5", "Deuteronomy 6 5", "Deuteronomy 6:5")
_t("యెహోషువ 1 1", "Joshua 1 1", "Joshua 1:1")
_t("న్యాయాధిపతులు 2 16", "Judges 2 16", "Judges 2:16")
_t("రూతు 1 1", "Ruth 1 1", "Ruth 1:1")
_t("ఎజ్రా 1 1", "Ezra 1 1", "Ezra 1:1")
_t("నెహెమ్యా 1 1", "Nehemiah 1 1", "Nehemiah 1:1")
_t("ఎస్తేరు 1 1", "Esther 1 1", "Esther 1:1")
_t("యోబు 1 1", "Job 1 1", "Job 1:1")
_t("సామెతలు 3 5", "Proverbs 3 5", "Proverbs 3:5")
_t("ప్రసంగి 1 1", "Ecclesiastes 1 1", "Ecclesiastes 1:1")
_t("పరమగీతము 1 1", "Song of Solomon 1 1", "Song of Solomon 1:1")
_t("యెషయా 53 5", "Isaiah 53 5", "Isaiah 53:5")
_t("యిర్మియా 29 11", "Jeremiah 29 11", "Jeremiah 29:11")
_t("విలాపవాక్యములు 3 22", "Lamentations 3 22", "Lamentations 3:22")
_t("యెహెజ్కేలు 37 1", "Ezekiel 37 1", "Ezekiel 37:1")
_t("దానియేలు 3 16", "Daniel 3 16", "Daniel 3:16")
_t("హోషేయా 11 1", "Hosea 11 1", "Hosea 11:1")
_t("యోవేలు 2 28", "Joel 2 28", "Joel 2:28")
_t("యోనా 1 17", "Jonah 1 17", "Jonah 1:17")
_t("మీకా 6 8", "Micah 6 8", "Micah 6:8")
_t("హబక్కూకు 3 1", "Habakkuk 3 1", "Habakkuk 3:1")
_t("మలాకీ 3 10", "Malachi 3 10", "Malachi 3:10")
_t("లూకా 2 1", "Luke 2 1", "Luke 2:1")
_t("మార్కు 1 1", "Mark 1 1", "Mark 1:1")
_t("అపొస్తలుల కార్యములు 1 8", "Acts 1 8", "Acts 1:8")
_t("యాకోబు 1 22", "James 1 22", "James 1:22")
_t("యూదా 1", "Jude 1", "Jude 1")

# ===== 15. Multiple corrections and complex flows =====
_t("John 3 15 sorry no 3 16", "John 3 16", "John 3:16")
_t("Romans 8 1 no 8 28 no 8 29", "Romans 8 29", "Romans 8:29")
_t("ఆమోసు 1 కాదు 2 కాదు 3 4", "Amos 3 4", "Amos 3:4")
_t("Matthew 5 no 6 no 7 8", "Matthew 7 8", "Matthew 7:8")

# ===== 16. Zero and edge numbers =====
_t("Genesis 1 0", "Genesis 1 0", None)  # chapter 1 verse 0 invalid
_t("Revelation 22 21", "Revelation 22 21", "Revelation 22:21")

# ===== 17. No book, chapter/verse markers only =====
_t("chapter 3 verse 16", "3 16", None)
_t("chapter 3", "3", None)
_t("verse 16", "16", None)
_t("chapter 12", "12", None)
_t("verse 4", "4", None)

# ===== 18. Big numbers =====
_t("John 151 1", "John 151 1", None)  # chapter > 150 → invalid
_t("John 3 200", "John 3 200", None)  # verse > 176 → invalid

# ===== 19. Song of Solomon edge cases =====
_t("song of solomon 1 1", "Song of Solomon 1 1", "Song of Solomon 1:1")
_t("song of songs 2 1", "Song of Solomon 2 1", "Song of Solomon 2:1")
_t("song 1 1", "Song of Solomon 1 1", "Song of Solomon 1:1")

# ===== 20. Telugu book + English number mix =====
_t("మత్తయి 3 16", "Matthew 3 16", "Matthew 3:16")
_t("యోహాను 3 16", "John 3 16", "John 3:16")
_t("కీర్తనలు 23 1", "Psalms 23 1", "Psalms 23:1")


def test_normalizer() -> int:
    failed = 0
    total = 0
    for inp, exp_norm, _ in NORMALIZER_TESTS:
        total += 1
        out = normalize_telugu_bible_reference(inp)
        if out != exp_norm:
            print(f"FAIL NORM [{total}]: {inp!r} -> {out!r} (expected {exp_norm!r})")
            failed += 1
    if failed:
        print(f"\nNormalizer: {total - failed}/{total} passed, {failed} FAILED")
    else:
        print(f"Normalizer: {total}/{total} passed")
    return failed


def test_parser() -> int:
    failed = 0
    total = 0
    for inp, _, exp_canon in NORMALIZER_TESTS:
        total += 1
        norm = normalize_telugu_bible_reference(inp)
        ref = parser.parse(norm)
        if exp_canon is None:
            if ref is not None:
                print(f"FAIL PARSE [{total}]: {inp!r} -> {ref.canonical!r} (expected None)")
                failed += 1
        else:
            if ref is None:
                print(f"FAIL PARSE [{total}]: {inp!r} -> None (expected {exp_canon!r})")
                failed += 1
            elif ref.canonical != exp_canon:
                print(f"FAIL PARSE [{total}]: {inp!r} -> {ref.canonical!r} (expected {exp_canon!r})")
                failed += 1
    if failed:
        print(f"\nParser: {total - failed}/{total} passed, {failed} FAILED")
    else:
        print(f"Parser: {total}/{total} passed")
    return failed


def test_intent() -> int:
    ref_count = 0
    nav_count = 0
    ignore_count = 0
    for inp, _, exp_canon in NORMALIZER_TESTS:
        intent, _ = detector.detect(inp)
        if exp_canon is not None:
            ref_count += 1
            if intent not in ("REFERENCE", "CROSS_REFERENCE"):
                print(f"FAIL INTENT: {inp!r} -> {intent!r} (expected REFERENCE/CROSS_REFERENCE)")
                return 1
        elif any(w in inp.lower() for w in ("next", "previous", "prev", "go back", "return", "continue",
                                              "తరువాతి", "ముందటి")):
            nav_count += 1
            if intent != "NAVIGATION":
                print(f"FAIL INTENT: {inp!r} -> {intent!r} (expected NAVIGATION)")
                return 1
        else:
            ignore_count += 1
    print(f"Intent: {ref_count + nav_count + ignore_count} checked ({ref_count} ref, {nav_count} nav, {ignore_count} ignore)")
    return 0


if __name__ == "__main__":
    nf = test_normalizer()
    pf = test_parser()
    ic = test_intent()
    total = nf + pf + ic
    if total:
        print(f"\n*** {total} FAILURES ***")
    else:
        print(f"\n*** ALL {len(NORMALIZER_TESTS)} TESTS PASSED ***")
    raise SystemExit(total)
