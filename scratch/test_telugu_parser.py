import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from parser import BibleReferenceParser
from intent_detector import IntentDetector
from sermon_context import parse_voice_command
from correction_engine import CorrectionEngine
from normalizer import TeluguNormalizer

def run_tests():
    parser = BibleReferenceParser()
    detector = IntentDetector()
    engine = CorrectionEngine()
    normalizer = TeluguNormalizer()

    # 1. Normalizer tests
    normalizer_tests = [
        ("ఆమోసుకు వ్రాసిన గ్రంథము మూడవ అధ్యాయం నాల్గవ వచనం", "Amos 3 4"),
        ("రోమీయులకు వ్రాసిన పత్రిక మూడవ అధ్యాయం", "Romans 3"),
        ("మత్తయి సువార్త అధ్యాయం మూడు", "Matthew 3"),
        ("మనము ఇప్పుడు John chapter 3 verse 16 చూద్దాం", "John 3 16"),
    ]

    print("--- Running Telugu Normalizer Tests ---")
    all_passed = True
    for text, expected_normalized in normalizer_tests:
        norm = normalizer.normalize(text)
        if norm != expected_normalized:
            print(f"FAILED: '{text}' -> '{norm}' (expected '{expected_normalized}')")
            all_passed = False
        else:
            print(f"PASSED: '{text}' -> '{norm}'")

    # 2. Correction Engine tests
    correction_tests = [
        ("Genesis 13 sorry 16 4", "Genesis 16 4"),
        ("Romans 8 no 9 28", "Romans 9 28"),
        ("Matthew actually John 3 16", "John 3 16"),
        ("ఆదికాండం 13 కాదు 16 4", "Genesis 16 4"),
        ("యోహాను మూడు... కాదు... నాలుగు... 16", "John 4 16"),
    ]

    print("\n--- Running Correction Engine Tests ---")
    for text, expected_corrected in correction_tests:
        corrected = engine.process_utterance(text)
        if corrected != expected_corrected:
            print(f"FAILED: '{text}' -> '{corrected}' (expected '{expected_corrected}')")
            all_passed = False
        else:
            print(f"PASSED: '{text}' -> '{corrected}'")

    # 3. Bible Reference parsing tests
    reference_tests = [
        ("మనము ఇప్పుడు John chapter 3 verse 16 చూద్దాం", "John 3:16", "John", 3, 16),
        ("యోహాను chapter three", "John", "John", 3, None),
        ("Matthew ఐదు", "Matthew", "Matthew", 5, None),
        ("Romans ఎనిమిది ఇరవై ఎనిమిది", "Romans 8:28", "Romans", 8, 28),
        ("కీర్తనలు 23", "Psalms", "Psalms", 23, None),
        ("Let's see యోహాను మూడు పదహారు", "John 3:16", "John", 3, 16),
        ("John మూడు పదహారు", "John 3:16", "John", 3, 16),
        ("యోహాను chapter 3", "John", "John", 3, None),
        ("Romans ఎనిమిది 28", "Romans 8:28", "Romans", 8, 28),
        ("Matthew chapter ఐదు", "Matthew", "Matthew", 5, None),
        ("Psalms పదిహేను మూడు", "Psalms 15:3", "Psalms", 15, 3),
        ("Genesis ఒకటి one", "Genesis 1:1", "Genesis", 1, 1),
    ]

    print("\n--- Running Reference Parsing Tests (via Normalizer) ---")
    for text, expected_canonical, expected_book, expected_chapter, expected_verse in reference_tests:
        norm = normalizer.normalize(text)
        ref = parser.parse(norm)
        if ref is None:
            print(f"FAILED: '{text}' -> None (expected {expected_canonical})")
            all_passed = False
        elif (ref.canonical != expected_canonical or
              ref.book != expected_book or
              ref.chapter != expected_chapter or
              ref.verse != expected_verse):
            print(f"FAILED: '{text}' -> {ref} (expected {expected_canonical}, {expected_book}, {expected_chapter}, {expected_verse})")
            all_passed = False
        else:
            print(f"PASSED: '{text}' -> {ref.canonical}")

    # 4. Fuzzy spelling tests
    fuzzy_tests = [
        ("యోహను 3 16", "John 3:16"),
        ("యోహాను 3 16", "John 3:16"),
        ("యోహానూ 3 16", "John 3:16"),
        ("యోహాన 3 16", "John 3:16"),
        ("రోమీయులకు 8 28", "Romans 8:28"),
        ("రోమీయులుకు 8 28", "Romans 8:28"),
        ("రోమియులకు 8 28", "Romans 8:28"),
    ]

    print("\n--- Running Fuzzy Spelling Tests ---")
    for text, expected_canonical in fuzzy_tests:
        norm = normalizer.normalize(text)
        ref = parser.parse(norm)
        if ref is None:
            print(f"FAILED: '{text}' -> None (expected {expected_canonical})")
            all_passed = False
        elif ref.canonical != expected_canonical:
            print(f"FAILED: '{text}' -> {ref.canonical} (expected {expected_canonical})")
            all_passed = False
        else:
            print(f"PASSED: '{text}' -> {ref.canonical}")

    # 5. Boundary / Chapter / Verse limits checks
    limits_tests = [
        ("Genesis 151 1", True), # Chapter too high (> 150)
        ("Genesis 1 177", True), # Verse too high (> 176)
        ("Genesis 1 176", False),
        ("Genesis 150 1", False),
    ]

    print("\n--- Running Limits Tests ---")
    for text, should_fail in limits_tests:
        norm = normalizer.normalize(text)
        ref = parser.parse(norm)
        if should_fail and ref is not None:
            print(f"FAILED: '{text}' parsed to {ref.canonical} but should have failed (limits)")
            all_passed = False
        elif not should_fail and ref is None:
            print(f"FAILED: '{text}' failed but should have parsed")
            all_passed = False
        else:
            print(f"PASSED: '{text}' -> {None if ref is None else ref.canonical}")

    # 6. Intent detection tests
    intent_tests = [
        ("మనము ఇప్పుడు John chapter 3 verse 16 చూద్దాం", "REFERENCE"),
        ("తరువాతి వచనం", "NAVIGATION"),
        ("next వచనం", "NAVIGATION"),
        ("Verse ఐదు", "NAVIGATION"),
        ("Chapter నాలుగు", "NAVIGATION"),
        ("యోహాను", "IGNORE"),
    ]

    print("\n--- Running Intent Detection Tests (on raw/corrected text) ---")
    for text, expected_intent in intent_tests:
        intent, conf = detector.detect(text)
        if intent != expected_intent:
            print(f"FAILED: '{text}' -> {intent} (expected {expected_intent})")
            all_passed = False
        else:
            print(f"PASSED: '{text}' -> {intent} (conf: {conf:.2f})")

    # 7. Voice navigation command parsing tests
    nav_tests = [
        ("తరువాతి వచనం", "next_verse"),
        ("next వచనం", "next_verse"),
        ("previous వచనం", "previous_verse"),
        ("ముందటి వచనం", "previous_verse"),
        ("తరువాతి అధ్యాయం", "next_chapter"),
        ("next అధ్యాయం", "next_chapter"),
        ("previous అధ్యాయం", "previous_chapter"),
        ("ముందటి అధ్యాయం", "previous_chapter"),
        ("వెనుకకు", "go_back"),
        ("వెనక్కి", "go_back"),
        ("తిరిగి వెళ్దాం", "return_to_passage"),
        ("Verse ఐదు", ("jump_to_verse", 5)),
        ("Chapter నాలుగు", ("jump_to_chapter", 4)),
    ]

    print("\n--- Running Voice Command Parsing Tests (on raw/corrected text) ---")
    for text, expected_cmd in nav_tests:
        cmd = parse_voice_command(text)
        if cmd != expected_cmd:
            print(f"FAILED: '{text}' -> {cmd} (expected {expected_cmd})")
            all_passed = False
        else:
            print(f"PASSED: '{text}' -> {cmd}")

    if all_passed:
        print("\nALL TESTS PASSED SUCCESSFULLY!")
    else:
        print("\nSOME TESTS FAILED!")

if __name__ == "__main__":
    run_tests()
