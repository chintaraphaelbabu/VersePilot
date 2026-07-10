from normalizer import normalize_telugu_bible_reference
from parser import BibleReferenceParser

def test_normalization():
    examples = {
        "ఆమోసుకు వ్రాసిన గ్రంథము మూడవ అధ్యాయం నాల్గవ వచనం": "Amos 3 4",
        "రోమీయులకు వ్రాసిన పత్రిక": "Romans",
        "మత్తయి సువార్త": "Matthew",
        "ఆమోసు": "Amos",
        "ఆమోసుకు": "Amos",
        "ఆమోసుకు వ్రాసిన పుస్తకం": "Amos",
        "రోమీయులకు వ్రాసిన పత్రిక 12వ అధ్యాయము 2వ వచనము": "Romans 12 2",
        "మత్తయి సువార్త మూడవ అధ్యాయం": "Matthew 3",
        "అధ్యాయం మూడు": "3",
        "వచనం నాలుగు": "4",
        # Corrections test
        "ఆమోసు మూడవ అధ్యాయం కాదు నాలుగవ అధ్యాయం": "Amos 4",
        "మత్తయి సువార్త 3 అధ్యాయం సారీ 4 అధ్యాయం 16 వచనం": "Matthew 4 16",
        # Fillers & Unknown words test
        "ఆమోసుకు మనము ఇప్పుడు వ్రాసిన గ్రంథము మూడవ కొంచెం అధ్యాయం నాల్గవ దయచేసి వచనం": "Amos 3 4"
    }

    print("Testing Telugu Normalizer...")
    all_passed = True
    for input_str, expected in examples.items():
        output = normalize_telugu_bible_reference(input_str)
        if expected in output or output == expected:
            print(f"PASS: '{input_str}' -> '{output}'")
        else:
            print(f"FAIL: '{input_str}' -> expected '{expected}', got '{output}'")
            all_passed = False
            
    # Also test with Parser integration
    print("\nTesting Parser Integration...")
    parser = BibleReferenceParser()
    test_cases = [
        ("ఆమోసుకు వ్రాసిన గ్రంథము మూడవ అధ్యాయం నాల్గవ వచనం", "Amos 3:4"),
        ("రోమీయులకు వ్రాసిన పత్రిక 12వ అధ్యాయము 2వ వచనము", "Romans 12:2"),
        ("మత్తయి సువార్త 3 అధ్యాయం 16 వచనం", "Matthew 3:16")
    ]
    for input_str, expected_ref in test_cases:
        res = parser.parse(input_str)
        if res and res.canonical == expected_ref:
            print(f"PASS: Parser '{input_str}' -> {res.canonical}")
        else:
            print(f"FAIL: Parser '{input_str}' -> expected {expected_ref}, got {res.canonical if res else 'None'}")
            all_passed = False

    if all_passed:
        print("\nAll tests passed successfully!")
    else:
        print("\nSome tests failed.")

if __name__ == "__main__":
    test_normalization()
