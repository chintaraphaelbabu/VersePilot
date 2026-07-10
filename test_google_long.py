from __future__ import annotations

import logging
import tempfile
import wave
import speech_recognition as sr
import sounddevice as sd
import numpy as np
from config import load_config
from mic import MicrophoneSelector, VoiceSegmentStream

logging.basicConfig(level=logging.INFO)
config = load_config()
selector = MicrophoneSelector(config.whisper_sample_rate)
mics = selector.list_microphones()
for item in mics:
    print(f"[{item.display}] {item.name}")
choice = int(input("\nChoose microphone: "))
device = selector.resolve_device(choice)

recognizer = sr.Recognizer()

print("\nSpeak your full sentence with reference. Press Ctrl+C after.")

try:
    with VoiceSegmentStream(config, device=device) as stream:
        for audio, start_time, end_time in stream.iter_segments():
            print(f"\nCaptured {len(audio)/16000:.2f}s")

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav_path = f.name
                with wave.open(f, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes((audio * 32767).astype(np.int16).tobytes())

            with sr.AudioFile(wav_path) as source:
                sr_audio = recognizer.record(source)

            # Telugu first
            try:
                te = recognizer.recognize_google(sr_audio, language="te-IN")
                print(f"GOOGLE te-IN: {te}")
            except Exception as e:
                print(f"GOOGLE te-IN failed: {e}")

            # English fallback
            try:
                en = recognizer.recognize_google(sr_audio, language="en-US")
                print(f"GOOGLE en-US: {en}")
            except Exception as e:
                print(f"GOOGLE en-US failed: {e}")

            # Auto-detect
            try:
                auto = recognizer.recognize_google(sr_audio)
                print(f"GOOGLE auto:  {auto}")
            except Exception as e:
                print(f"GOOGLE auto failed: {e}")

            break
except KeyboardInterrupt:
    print("Stopped")
