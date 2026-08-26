import unittest

import numpy as np

from versepilot.correction_engine import CorrectionEngine, FUZZY_STOPLIST
from versepilot.intent_detector import IntentDetector
from versepilot.mic import enhance_audio
from versepilot.reference_builder import ReferenceBuilder


class TestRegressionBugs(unittest.TestCase):
    """Regression tests for bugs found in the 4-fix audit."""

    def test_correction_engine_resets_end_verse(self):
        """Bug 1: BOOK: token must clear stale end_verse."""
        engine = CorrectionEngine()
        engine.process_utterance("Psalms 100 1 2")  # ch=100, v=1, end=2
        self.assertEqual(engine.ref.end_verse, 2)
        engine.process_utterance("John 3")
        self.assertIsNone(engine.ref.end_verse,
                          "end_verse leaked from Psalms into John ref")

    def test_fuzzy_stoplist_blocks_telugu_false_positive(self):
        """Bug 3: Telugu word పాయింట్స్ must not fuzzy-match a book."""
        self.assertIn("పాయింట్స్", FUZZY_STOPLIST)
        engine = CorrectionEngine()
        result = engine.process_utterance("పాయింట్స్")
        self.assertEqual(result, "పాయింట్స్",  # passthrough, no book matched
                         "పాయింట్స్ should not match Psalms")

    def test_intent_detector_rejects_sermon_exposition(self):
        """Bug 4: Long text without any book token must not return REFERENCE."""
        detector = IntentDetector()
        text = "ఈ విషయములో దేవుని వాక్యము ఏమి చెప్పుచున్నది"
        intent, conf = detector.detect(text)
        self.assertEqual(intent, "IGNORE",
                         "Sermon exposition without book must not be REFERENCE")

    def test_reference_builder_complete_produces_canonical(self):
        """Bug 2: Builder must produce canonical string when COMPLETE."""
        builder = ReferenceBuilder()
        builder.process("John 3")
        builder.process("16")
        builder.process("nundi")
        builder.process("18")
        self.assertTrue(builder.is_complete())
        self.assertIsNotNone(builder.verse)
        ref = builder.current_reference()
        self.assertEqual(ref.canonical, "John 3:16-18",
                         "Complete ref must produce scannable canonical string")

    def test_audio_enhancement_reduces_low_frequency_rumble(self):
        samples = np.arange(16000) / 16000
        rumble = np.sin(2 * np.pi * 50 * samples).astype(np.float32)
        cleaned = enhance_audio(rumble, 16000)
        self.assertLess(float(np.sqrt(np.mean(cleaned ** 2))), 0.2)


if __name__ == "__main__":
    unittest.main()