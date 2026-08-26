"""Generate church_corpus.yaml from known-good test data plus new examples."""
from __future__ import annotations

import yaml

entries: list[dict] = []

def add(inp: str, book: str | None = None, chapter: int | None = None,
        verse: int | None = None, end_verse: int | None = None) -> None:
    d: dict = {"input": inp}
    if book is not None:
        d["book"] = book
    if chapter is not None:
        d["chapter"] = chapter
    if verse is not None:
        d["verse"] = verse
    if end_verse is not None:
        d["end_verse"] = end_verse
    entries.append(d)


# ===== 1. English references =====
add("John 3 16", "John", 3, 16)
add("John 3:16", "John", 3, 16)
add("Genesis 1 1", "Genesis", 1, 1)
add("Matthew 5 3", "Matthew", 5, 3)
add("Psalm 23", "Psalms", 23)
add("Psalms 23 1", "Psalms", 23, 1)
add("Proverbs 3 5", "Proverbs", 3, 5)
add("Exodus 20 1 17", "Exodus", 20, 1, 17)
add("Romans 8 28", "Romans", 8, 28)
add("Revelation 22 21", "Revelation", 22, 21)
add("Acts 2 38", "Acts", 2, 38)
add("Hebrews 11 1", "Hebrews", 11, 1)
add("Genesis 1 26 28", "Genesis", 1, 26, 28)
add("Matthew 28 19 20", "Matthew", 28, 19, 20)
add("Psalm 119 105", "Psalms", 119, 105)
add("Isaiah 53 5", "Isaiah", 53, 5)
add("Jeremiah 29 11", "Jeremiah", 29, 11)
add("Ezekiel 37 1", "Ezekiel", 37, 1)
add("Daniel 3 16", "Daniel", 3, 16)
add("Hosea 11 1", "Hosea", 11, 1)
add("Joel 2 28", "Joel", 2, 28)
add("Amos 3 4", "Amos", 3, 4)
add("Jonah 1 17", "Jonah", 1, 17)
add("Micah 6 8", "Micah", 6, 8)
add("Zechariah 9 9", "Zechariah", 9, 9)
add("Malachi 3 10", "Malachi", 3, 10)
add("Mark 1 1", "Mark", 1, 1)
add("Luke 2 1", "Luke", 2, 1)
add("Acts 1 8", "Acts", 1, 8)
add("Galatians 5 22", "Galatians", 5, 22)
add("Ephesians 2 8", "Ephesians", 2, 8)
add("Philippians 4 13", "Philippians", 4, 13)
add("Colossians 3 16", "Colossians", 3, 16)
add("Titus 2 11", "Titus", 2, 11)
add("Philemon 1 4", "Philemon", 1, 4)
add("James 1 22", "James", 1, 22)
add("John 3:16-18", "John", 3, 16, 18)
add("Romans 8:28-30", "Romans", 8, 28, 30)

# ===== 2. English with chapter/verse markers =====
add("John chapter 3 verse 16", "John", 3, 16)
add("Genesis chapter 1 verse 1", "Genesis", 1, 1)
add("Romans chapter 8", "Romans", 8)
add("Matthew chapter 5 verse 3", "Matthew", 5, 3)
add("Psalm chapter 23 verse 1", "Psalms", 23, 1)
add("Proverbs chapter 3 verse 5", "Proverbs", 3, 5)
add("Isaiah chapter 53 verse 5", "Isaiah", 53, 5)

# ===== 3. English with number words =====
add("first John 3 16", "1 John", 3, 16)
add("second Corinthians 5 17", "2 Corinthians", 5, 17)
add("first Timothy 3 16", "1 Timothy", 3, 16)
add("second Timothy 3 16", "2 Timothy", 3, 16)
add("first Peter 3 15", "1 Peter", 3, 15)
add("second Peter 1 4", "2 Peter", 1, 4)
add("third John 1", "3 John", 1)
add("first Corinthians 13", "1 Corinthians", 13)
add("second Thessalonians 3", "2 Thessalonians", 3)

# ===== 4. English book-only (no chapter) =====
add("Psalms")
add("Genesis")
add("Romans")
add("Revelation")
add("Proverbs")
add("Isaiah")
add("Hebrews")

# ===== 5. English chapter-only =====
add("Genesis 1", "Genesis", 1)
add("John 3", "John", 3)
add("Psalms 23", "Psalms", 23)
add("Romans 8", "Romans", 8)
add("Proverbs 3", "Proverbs", 3)
add("Isaiah 53", "Isaiah", 53)
add("Revelation 22", "Revelation", 22)

# ===== 6. English abbreviations =====
add("Gen 1 1", "Genesis", 1, 1)
add("Ex 20 1", "Exodus", 20, 1)
add("Lev 19 18", "Leviticus", 19, 18)
add("Num 6 24", "Numbers", 6, 24)
add("Deut 6 5", "Deuteronomy", 6, 5)
add("Josh 1 1", "Joshua", 1, 1)
add("Ps 23 1", "Psalms", 23, 1)
add("Prov 3 5", "Proverbs", 3, 5)
add("Isa 53 5", "Isaiah", 53, 5)
add("Jer 29 11", "Jeremiah", 29, 11)
add("Matt 5 3", "Matthew", 5, 3)
add("Heb 11 1", "Hebrews", 11, 1)
add("Rev 22 21", "Revelation", 22, 21)
add("1 Cor 13", "1 Corinthians", 13)
add("2 Cor 5 17", "2 Corinthians", 5, 17)
add("1 Tim 3 16", "1 Timothy", 3, 16)
add("2 Tim 3 16", "2 Timothy", 3, 16)

# ===== 7. Telugu references (number words) =====
add("ఆమోసు మూడు నాలుగు", "Amos", 3, 4)
add("ఆమోసు మూడు నాల్గవ వచనం", "Amos", 3, 4)
add("మత్తయి మూడు పదహారు", "Matthew", 3, 16)
add("యోహాను మూడు పదహారు", "John", 3, 16)
add("ఆదికాండము ఒకటి ఒకటి", "Genesis", 1, 1)
add("కీర్తనలు ఇరవై మూడు", "Psalms", 23)
add("కీర్తనలు ఇరవై మూడు ఒకటి", "Psalms", 23, 1)
add("రోమీయులకు ఎనిమిది ఇరవై ఎనిమిది", "Romans", 8, 28)
add("ప్రకటన ఇరవై రెండు ఇరవై ఒకటి", "Revelation", 22, 21)
add("అపొస్తలుల కార్యములు రెండు ముప్పై ఎనిమిది", "Acts", 2, 38)
add("హెబ్రీయులకు పదకొండు ఒకటి", "Hebrews", 11, 1)
add("యోహాను మూడు పదహారు", "John", 3, 16)
add("యెషయా యాభై మూడు ఐదు", "Isaiah", 53, 5)
add("దానియేలు మూడు పదహారు", "Daniel", 3, 16)
add("యిర్మియా ఇరవై తొమ్మిది పదకొండు", "Jeremiah", 29, 11)

# ===== 8. Telugu references (digits) =====
add("యోహాను 3 16", "John", 3, 16)
add("మత్తయి 5 3", "Matthew", 5, 3)
add("కీర్తనలు 23 1", "Psalms", 23, 1)
add("ఆదికాండము 1 1", "Genesis", 1, 1)
add("రోమీయులకు 8 28", "Romans", 8, 28)
add("ప్రకటన 22 21", "Revelation", 22, 21)
add("అపొస్తలుల కార్యములు 2 38", "Acts", 2, 38)
add("హెబ్రీయులకు 11 1", "Hebrews", 11, 1)

# ===== 9. Telugu with chapter/verse markers =====
add("మత్తయి మూడవ అధ్యాయం పదహారవ వచనం", "Matthew", 3, 16)
add("యోహాను మూడవ అధ్యాయము పదహారవ వచనము", "John", 3, 16)
add("ఆమోసు మూడవ అధ్యాయం నాల్గవ వచనం", "Amos", 3, 4)
add("రోమీయులకు ఎనిమిదవ అధ్యాయము ఇరవై ఎనిమిదవ వచనము", "Romans", 8, 28)
add("కీర్తనలు ఇరవై మూడవ అధ్యాయము ఒకటవ వచనము", "Psalms", 23, 1)
add("మత్తయి సువార్త మూడవ అధ్యాయం", "Matthew", 3)

# ===== 10. Telugu with digit ordinals =====
add("రోమీయులకు 12వ అధ్యాయము 2వ వచనము", "Romans", 12, 2)
add("మత్తయి 3వ అధ్యాయం 16వ వచనం", "Matthew", 3, 16)
add("కీర్తనలు 23వ అధ్యాయము 1వ వచనము", "Psalms", 23, 1)
add("యోహాను 3వ అధ్యాయము 16వ వచనము", "John", 3, 16)
add("ఆదికాండము 1వ అధ్యాయము 1వ వచనము", "Genesis", 1, 1)

# ===== 11. Telugu book-only =====
add("ఆమోసు")
add("మత్తయి")
add("రోమీయులకు")
add("కీర్తనలు")
add("ప్రకటన")
add("యోహాను")
add("ఆదికాండము")
add("హెబ్రీయులకు")

# ===== 12. Telugu chapter-only =====
add("ఆమోసు మూడు", "Amos", 3)
add("మత్తయి మూడు", "Matthew", 3)
add("కీర్తనలు ఇరవై మూడు", "Psalms", 23)
add("యోహాను మూడు", "John", 3)
add("రోమీయులకు ఎనిమిది", "Romans", 8)
add("ఆదికాండము ఒకటి", "Genesis", 1)

# ===== 13. Mixed Telugu-English =====
add("Romans ఎనిమిది 28", "Romans", 8, 28)
add("John మూడు పదహారు", "John", 3, 16)
add("Matthew అయిదు మూడు", "Matthew", 5, 3)
add("Psalms ఇరవై మూడు ఒకటి", "Psalms", 23, 1)
add("Acts రెండు ముప్పై ఎనిమిది", "Acts", 2, 38)
add("Revelation ఇరవై రెండు ఇరవై ఒకటి", "Revelation", 22, 21)
add("Genesis ఒకటి 1", "Genesis", 1, 1)
add("Romans chapter ఎనిమిది verse ఇరవై ఎనిమిది", "Romans", 8, 28)
add("Matthew chapter అయిదు verse మూడు", "Matthew", 5, 3)
add("John మూడు chapter పదహారు", "John", 3, 16)
add("Psalms chapter ఇరవై మూడు", "Psalms", 23)
add("Isaiah chapter యాభై మూడు verse ఐదు", "Isaiah", 53, 5)

# ===== 14. Book suffixes (Telugu) =====
add("ఆమోసుకు")
add("రూతుకు")
add("యోబుకు")
add("యెహోషువకు")
add("దానియేలుకు")
add("ఆమోసుకు మూడు నాలుగు", "Amos", 3, 4)
add("రోమీయులకు వ్రాసిన పత్రిక 12 2", "Romans", 12, 2)

# ===== 15. Telugu spoken variants (abbreviations) =====
add("ఆది 1 1", "Genesis", 1, 1)
add("నిర్గమ 20 1", "Exodus", 20, 1)
add("ద్వితీయ 6 5", "Deuteronomy", 6, 5)
add("కీర్త 23 1", "Psalms", 23, 1)
add("యెహో 1 1", "Joshua", 1, 1)
add("ప్రక 22 21", "Revelation", 22, 21)
add("రోమీ 8 28", "Romans", 8, 28)
add("గలతీ 3 1", "Galatians", 3, 1)
add("మత్త 3 16", "Matthew", 3, 16)
add("యోహ 3 16", "John", 3, 16)
add("దాని 3 16", "Daniel", 3, 16)
add("హెబ్రీ 11 1", "Hebrews", 11, 1)
add("యూదా 1", "Jude", 1)

# ===== 16. Telugu book aliases (full names) =====
add("ఆదికాండము 1 1", "Genesis", 1, 1)
add("నిర్గమకాండము 20 1", "Exodus", 20, 1)
add("లేవీయకాండము 19 18", "Leviticus", 19, 18)
add("సంఖ్యాకాండము 6 24", "Numbers", 6, 24)
add("ద్వితీయోపదేశకాండము 6 5", "Deuteronomy", 6, 5)
add("యెహోషువ 1 1", "Joshua", 1, 1)
add("న్యాయాధిపతులు 2 16", "Judges", 2, 16)
add("రూతు 1 1", "Ruth", 1, 1)
add("ఎజ్రా 1 1", "Ezra", 1, 1)
add("నెహెమ్యా 1 1", "Nehemiah", 1, 1)
add("ఎస్తేరు 1 1", "Esther", 1, 1)
add("యోబు 1 1", "Job", 1, 1)
add("సామెతలు 3 5", "Proverbs", 3, 5)
add("ప్రసంగి 1 1", "Ecclesiastes", 1, 1)
add("పరమగీతము 1 1", "Song of Solomon", 1, 1)
add("యెషయా 53 5", "Isaiah", 53, 5)
add("యిర్మియా 29 11", "Jeremiah", 29, 11)
add("విలాపవాక్యములు 3 22", "Lamentations", 3, 22)
add("యెహెజ్కేలు 37 1", "Ezekiel", 37, 1)
add("దానియేలు 3 16", "Daniel", 3, 16)
add("హోషేయా 11 1", "Hosea", 11, 1)
add("యోవేలు 2 28", "Joel", 2, 28)
add("యోనా 1 17", "Jonah", 1, 17)
add("మీకా 6 8", "Micah", 6, 8)
add("హబక్కూకు 3 1", "Habakkuk", 3, 1)
add("మలాకీ 3 10", "Malachi", 3, 10)
add("లూకా 2 1", "Luke", 2, 1)
add("మార్కు 1 1", "Mark", 1, 1)
add("అపొస్తలుల కార్యములు 1 8", "Acts", 1, 8)
add("యాకోబు 1 22", "James", 1, 22)
add("యూదా 1", "Jude", 1)

# ===== 17. Corrections - English =====
add("Genesis 13 sorry 16 4", "Genesis", 16, 4)
add("John 3 no 4 16", "John", 4, 16)
add("Romans 8 no 9 28", "Romans", 9, 28)
add("John 3 15 sorry 16", "John", 3, 16)
add("Romans 8 1 no 8 28", "Romans", 8, 28)
add("Romans 8 28 no 8 29", "Romans", 8, 29)
add("John 3 15 sorry no 3 16", "John", 3, 16)
add("Matthew 5 no 6 no 7 8", "Matthew", 7, 8)

# ===== 18. Corrections - Telugu =====
add("ఆమోసు మూడవ అధ్యాయం కాదు నాలుగవ అధ్యాయం", "Amos", 4)
add("మత్తయి సువార్త 3 అధ్యాయం సారీ 4 అధ్యాయం 16 వచనం", "Matthew", 4, 16)
add("ఆమోసు మూడు కాదు నాలుగు", "Amos", 4)
add("మత్తయి మూడు సారీ నాలుగు", "Matthew", 4)
add("ఆమోసుకు కాదు యోనా")
add("Romans 8 28 కాదు 8 29", "Romans", 8, 29)
add("యోహాను 3 16 సారీ 3 17", "John", 3, 17)
add("ఆమోసు 3 4 ఆ 3 5", "Amos", 3, 5)
add("Romans 8 1 no 8 28 no 8 29", "Romans", 8, 29)
add("ఆమోసు 1 కాదు 2 కాదు 3 4", "Amos", 3, 4)
add("మత్తయి 5 కాదు 6 కాదు 7 8", "Matthew", 7, 8)

# ===== 19. Corrections with context =====
add("no it is John 3 16", "John", 3, 16)
add("I meant Romans 8 28", "Romans", 8, 28)
add("sorry actually Genesis 1 1", "Genesis", 1, 1)
add("no sorry I mean Matthew 5 3", "Matthew", 5, 3)
add("I said Acts 2 no wait Acts 2 38", "Acts", 2, 38)

# ===== 20. Cross references =====
add("see also John 3 16", "John", 3, 16)
add("compare Romans 8 28", "Romans", 8, 28)
add("చూడండి మత్తయి 5 3", "Matthew", 5, 3)
add("cross reference Genesis 1 1", "Genesis", 1, 1)
add("look at Psalms 23", "Psalms", 23)
add("see also John 3", "John", 3)
add("పోల్చి రోమీయులకు 8 28", "Romans", 8, 28)
add("compare with Ephesians 2 8", "Ephesians", 2, 8)
add("see also Matthew 28 19 20", "Matthew", 28, 19, 20)

# ===== 21. Numbered books - English =====
add("1 Timothy 3 16", "1 Timothy", 3, 16)
add("2 Timothy 3 16", "2 Timothy", 3, 16)
add("1 Corinthians 13", "1 Corinthians", 13)
add("2 Corinthians 5 17", "2 Corinthians", 5, 17)
add("1 Kings 18", "1 Kings", 18)
add("2 Kings 2", "2 Kings", 2)
add("1 Samuel 3", "1 Samuel", 3)
add("2 Samuel 3", "2 Samuel", 3)
add("1 Chronicles 1", "1 Chronicles", 1)
add("2 Chronicles 1", "2 Chronicles", 1)
add("1 Peter 3 15", "1 Peter", 3, 15)
add("2 Peter 1 4", "2 Peter", 1, 4)
add("1 John 1", "1 John", 1)
add("2 John 1", "2 John", 1)
add("3 John 1", "3 John", 1)
add("1 Thessalonians 5", "1 Thessalonians", 5)
add("2 Thessalonians 3", "2 Thessalonians", 3)
add("1 Timothy 4 12", "1 Timothy", 4, 12)
add("2 Timothy 1 7", "2 Timothy", 1, 7)

# ===== 22. Numbered books - Telugu =====
add("1 సమూయేలు 3", "1 Samuel", 3)
add("2 సమూయేలు 3", "2 Samuel", 3)
add("1 కొరింథీయులకు 13", "1 Corinthians", 13)
add("2 కొరింథీయులకు 5 17", "2 Corinthians", 5, 17)
add("1 తిమోతికి 3 16", "1 Timothy", 3, 16)
add("2 తిమోతికి 3 16", "2 Timothy", 3, 16)
add("1 పేతురు 3 15", "1 Peter", 3, 15)
add("2 పేతురు 1 4", "2 Peter", 1, 4)
add("1 యోహాను 1", "1 John", 1)
add("2 యోహాను 1", "2 John", 1)
add("3 యోహాను 1", "3 John", 1)
add("1 రాజులు 18", "1 Kings", 18)
add("2 రాజులు 2", "2 Kings", 2)

# ===== 23. Numbered books with Telugu number prefix =====
add("మొదటి తిమోతికి 3 16", "1 Timothy", 3, 16)
add("రెండవ తిమోతికి 3 16", "2 Timothy", 3, 16)
add("మొదటి పేతురు 3 15", "1 Peter", 3, 15)
add("రెండవ పేతురు 1 4", "2 Peter", 1, 4)
add("మూడవ యోహాను 1", "3 John", 1)
add("మొదటి కొరింథీయులకు 13", "1 Corinthians", 13)
add("రెండవ కొరింథీయులకు 5 17", "2 Corinthians", 5, 17)

# ===== 24. Numbered books with base names (no prefix) =====
add("Timothy 3 16", "1 Timothy", 3, 16)
add("Corinthians 13", "1 Corinthians", 13)
add("Samuel 3", "1 Samuel", 3)
add("Peter 3 15", "1 Peter", 3, 15)
add("John 1", "John", 1)  # Gospel, not epistle

# ===== 25. Single-chapter books =====
add("Jude 1", "Jude", 1)
add("Philemon 1", "Philemon", 1)
add("Philemon 1 4", "Philemon", 1, 4)
add("Obadiah 1", "Obadiah", 1)
add("2 John 1", "2 John", 1)
add("3 John 1", "3 John", 1)

# ===== 26. Filler words and noise =====
add("ఆమోసుకు వ్రాసిన గ్రంథము మూడవ అధ్యాయం నాల్గవ వచనం", "Amos", 3, 4)
add("రోమీయులకు వ్రాసిన పత్రిక 12వ అధ్యాయము 2వ వచనము", "Romans", 12, 2)
add("మత్తయి సువార్త మూడవ అధ్యాయం", "Matthew", 3)
add("యోహాను సువార్త మూడవ అధ్యాయము పదహారవ వచనము", "John", 3, 16)
add("Romans the epistle to the 8 28", "Romans", 8, 28)
add("the book of Genesis 1 1", "Genesis", 1, 1)
add("మనము ఇప్పుడు ఆమోసు మూడు నాలుగు చూద్దాం", "Amos", 3, 4)
add("ఇప్పుడు మత్తయి మూడు పదహారు తిరగండి", "Matthew", 3, 16)
add("కొంచెం యోహాను 3 16 దయచేసి", "John", 3, 16)
add("మనము రోమీయులకు ఎనిమిది ఇరవై ఎనిమిది చూద్దాం", "Romans", 8, 28)

# ===== 27. Long church names =====
add("ఆమోసుకు వ్రాసిన గ్రంథము")
add("రోమీయులకు వ్రాసిన పత్రిక")
add("మత్తయి సువార్త")
add("మొదటి కొరింథీయులకు వ్రాసిన పత్రిక 13", "1 Corinthians", 13)
add("యోహాను సువార్త 3 16", "John", 3, 16)
add("యెషయా గ్రంథము 53 5", "Isaiah", 53, 5)
add("కీర్తనల గ్రంథము 23 1", "Psalms", 23, 1)
add("ప్రకటన గ్రంథము 22 21", "Revelation", 22, 21)
add("మత్తయి వ్రాసిన సువార్త మూడవ అధ్యాయం పదహారవ వచనం", "Matthew", 3, 16)

# ===== 28. Verse ranges =====
add("John 3 16 18", "John", 3, 16, 18)
add("John 3:16-18", "John", 3, 16, 18)
add("Romans 8 28 30", "Romans", 8, 28, 30)
add("Romans 8:28-30", "Romans", 8, 28, 30)
add("Genesis 1 26 28", "Genesis", 1, 26, 28)
add("Matthew 28 19 20", "Matthew", 28, 19, 20)
add("Psalms 119 105", "Psalms", 119, 105)
add("Ephesians 2 8 10", "Ephesians", 2, 8, 10)
add("Isaiah 53 4 6", "Isaiah", 53, 4, 6)

# ===== 29. Navigation commands (no reference) =====
add("next verse")
add("previous verse")
add("next chapter")
add("previous chapter")
add("go back")
add("go back to passage")
add("continue")
add("continue reading")
add("return to the passage")
add("verse 5")
add("chapter 3")
add("తరువాతి వచనం")
add("తరువాతి అధ్యాయం")
add("next వచనం")
add("previous వచనం")
add("ముందటి వచనం")
add("ముందటి అధ్యాయం")
add("next అధ్యాయం")
add("prev verse")
add("prev chapter")
add("go to verse 10")
add("go to chapter 5")
add("turn to the next verse")

# ===== 30. Non-Bible / pastor speech (no reference) =====
add("let us pray")
add("good morning everyone")
add("amen")
add("hallelujah")
add("please turn to your neighbor")
add("let us stand")
add("thank you")
add("praise the Lord")
add("we will now read")
add("please be seated")
add("close your eyes")
add("thank you Jesus")
add("ఆమెను")
add("మన ప్రార్థన")
add("నమస్కారము")
add("please open your Bibles")
add("let us worship the Lord")
add("can we sing together")
add("let me pray for you")
add("father we thank you")
add("in Jesus name we pray")
add("lift up your hands")
add("give thanks unto the Lord")
add("praise him")

# ===== 31. Zero and invalid edge cases =====
add("Revelation 22 21", "Revelation", 22, 21)
add("John 151 1")  # chapter > 150 → invalid
add("John 3 200")  # verse > 176 → invalid
add("Genesis 1 0")  # verse 0 → invalid

# ===== 32. No book, numbers only =====
add("3 16")
add("8 28")
add("23")
add("1 1")
add("12 2")

# ===== 33. Chapter/verse markers without book =====
add("chapter 3 verse 16")
add("chapter 3")
add("chapter 12")
add("verse 4")
add("verse 16")

# ===== 34. Song of Solomon =====
add("song of solomon 1 1", "Song of Solomon", 1, 1)
add("song of songs 2 1", "Song of Solomon", 2, 1)
add("song 1 1", "Song of Solomon", 1, 1)

# ===== 35. Various corrections complex =====
add("John 3 15 sorry no 3 16", "John", 3, 16)
add("Romans 8 1 no 8 28 no 8 29", "Romans", 8, 29)
add("ఆమోసు 1 కాదు 2 కాదు 3 4", "Amos", 3, 4)
add("Matthew 5 no 6 no 7 8", "Matthew", 7, 8)
add("Romans 8 first no Romans 9 28", "Romans", 9, 28)
add("John 3 15 no 16 no 17", "John", 3, 17)

# ===== 36. "first of" pattern =====
add("first of John 3 16", "1 John", 3, 16)
add("first of Corinthians 13", "1 Corinthians", 13)
add("first of Peter 3 15", "1 Peter", 3, 15)

# ===== 37. Navigation with book ref (should still produce ref) =====
add("go to Romans 8 28", "Romans", 8, 28)
add("turn to John 3 16", "John", 3, 16)
add("open to Psalms 23", "Psalms", 23)
add("read Matthew 5 3", "Matthew", 5, 3)

# ===== 38. Pastor mid-sermon interjections =====
add("verse 16 is so powerful")
add("look at chapter 3 verse 16")
add("Romans 8 28 is my favorite", "Romans", 8, 28)
add("John 3 16 reminds us", "John", 3, 16)
add("in Matthew 5 3 we see", "Matthew", 5, 3)
add("going back to Psalms 23", "Psalms", 23)
add("as we read in Acts 2 38", "Acts", 2, 38)
add("remember Ephesians 2 8", "Ephesians", 2, 8)
add("as it says in Isaiah 53 5", "Isaiah", 53, 5)
add("the gospel of John 3 16", "John", 3, 16)

# ===== 39. Telugu pastor interjections =====
add("యోహాను 3 16 చూడండి", "John", 3, 16)
add("మత్తయి 5 3 ఎంత అందమైన వచనం", "Matthew", 5, 3)
add("రోమీయులకు 8 28 మనకు గుర్తుంచుకోండి", "Romans", 8, 28)
add("కీర్తనలు 23 1 ప్రభువు నా కాపరి", "Psalms", 23, 1)
add("ఆదికాండము 1 1 దేవుడు ఆకాశాన్ని", "Genesis", 1, 1)
add("యెషయా 53 5 ఆయన దెబ్బలతో", "Isaiah", 53, 5)

# ===== 40. English spoken numbers for books =====
add("first Timothy 3 16", "1 Timothy", 3, 16)
add("second Timothy 3 16", "2 Timothy", 3, 16)
add("first Corinthians 13", "1 Corinthians", 13)
add("second Corinthians 5 17", "2 Corinthians", 5, 17)
add("third John 1", "3 John", 1)
add("first Thessalonians 5", "1 Thessalonians", 5)
add("second Thessalonians 3", "2 Thessalonians", 3)
add("first Kings 18", "1 Kings", 18)
add("second Kings 2", "2 Kings", 2)
add("first Samuel 3", "1 Samuel", 3)
add("second Samuel 3", "2 Samuel", 3)

# ===== 41. English spoken numbers for chapters/verses =====
add("John chapter three verse sixteen", "John", 3, 16)
add("Psalms twenty three", "Psalms", 23)
add("Romans eight twenty eight", "Romans", 8, 28)
add("Matthew five three", "Matthew", 5, 3)
add("Genesis one one", "Genesis", 1, 1)
add("Acts two thirty eight", "Acts", 2, 38)
add("Hebrews eleven one", "Hebrews", 11, 1)

# ===== 42. Realistic pastor reading patterns =====
add("our passage today is John 3 16", "John", 3, 16)
add("the scripture reading is Romans 8", "Romans", 8)
add("let's read from Psalms 23 1", "Psalms", 23, 1)
add("turn in your Bibles to Matthew 5", "Matthew", 5)
add("I'll be reading from Ephesians 2 8 10", "Ephesians", 2, 8, 10)
add("our text is from Genesis 1 1", "Genesis", 1, 1)
add("the word of God from Acts 2 38", "Acts", 2, 38)
add("we continue in Romans 8 28 30", "Romans", 8, 28, 30)
add("today's message from Philippians 4 13", "Philippians", 4, 13)

# ===== 43. Book only with numbers in context words =====
add("read from Romans today")
add("the Gospel of John")
add("the book of Psalms")
add("Paul's letter to the Romans")
add("let us turn to Romans")
add("we were in Romans last week")
add("Paul writes in Romans")
add("as we saw in Matthew")
add("the prophet Isaiah says")

# ===== 44. Verse ranges in natural language =====
add("from verse 16 to 18")
add("John 3 16 through 18", "John", 3, 16, 18)
add("Romans 8 verses 28 to 30", "Romans", 8, 28, 30)
add("first Corinthians 13 4 8", "1 Corinthians", 13, 4, 8)
add("Proverbs 3 5 6", "Proverbs", 3, 5, 6)
add("Ephesians 6 10 18", "Ephesians", 6, 10, 18)

# ===== 45. Mixed language corrections =====
add("Romans 8 సారీ 9 28", "Romans", 9, 28)
add("ఆదికాండము 1 no 2 3", "Genesis", 2, 3)
add("John 3 16 కాదు 4 16", "John", 4, 16)
add("Matthew 5 సారీ 6 3", "Matthew", 6, 3)
add("Psalms 23 కాదు 24", "Psalms", 24)

# ===== 46. Dual references in one utterance =====
# Parser picks the last complete reference
add("first reading John 3 16 then Romans 8 28", "Romans", 8, 28)
add("we read Acts 2 38 and then Romans 8 28", "Romans", 8, 28)

# ===== 47. Ordinal date-like patterns =====
add("Revelation 22 21", "Revelation", 22, 21)
add("John 1 1", "John", 1, 1)
add("1 Timothy 1 1", "1 Timothy", 1, 1)

# ===== 48. "chapter" and "verse" mixed =====
add("John 3 verse 16", "John", 3, 16)
add("John chapter 3 16", "John", 3, 16)
add("Romans 8 verse 28", "Romans", 8, 28)
add("Psalms chapter 23 verse 1", "Psalms", 23, 1)
add("Matthew chapter 5 3", "Matthew", 5, 3)

# ===== 49. Utterances with "chapter" and "verse" markers in Telugu =====
add("మత్తయి మూడు అధ్యాయం పదహారు వచనం", "Matthew", 3, 16)
add("యోహాను మూడవ అధ్యాయం పదహారు", "John", 3, 16)
add("రోమీయులకు ఎనిమిది అధ్యాయం ఇరవై ఎనిమిది వచనం", "Romans", 8, 28)

# ===== 50. Extra realistic examples =====
add("Psalm 23 the Lord is my shepherd", "Psalms", 23)
add("John 11 35 Jesus wept", "John", 11, 35)
add("Romans 12 1 2 living sacrifice", "Romans", 12, 1, 2)
add("Philippians 4 6 7 peace of God", "Philippians", 4, 6, 7)
add("Proverbs 3 5 6 trust in the Lord", "Proverbs", 3, 5, 6)
add("1 John 1 9 confess our sins", "1 John", 1, 9)
add("Romans 8 28 is my favorite", "Romans", 8, 28)
add("Romans 8 28 is such a comfort", "Romans", 8, 28)
add("I am reading John 3 16 today", "John", 3, 16)
add("this is from Proverbs 3 5", "Proverbs", 3, 5)



# Write YAML
with open("data/church_corpus.yaml", "w", encoding="utf-8") as f:
    f.write("# Church Sermon Utterance Corpus\n")
    f.write("# Each entry: input text + expected parser output.\n")
    f.write("# book=null (or omitted) means no reference expected.\n")
    f.write("# Add new entries at the end as you collect from real sermons.\n")
    f.write("---\n")
    yaml.dump(entries, f, allow_unicode=True, default_flow_style=False,
              sort_keys=False, width=120, indent=2)

print(f"Generated data/church_corpus.yaml with {len(entries)} entries")
