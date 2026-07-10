from __future__ import annotations

import io
import logging
import tempfile
import wave
import speech_recognition as sr
import sounddevice as sd
import numpy as np
from config import load_config
from mic import MicrophoneSelector, VoiceSegmentStream

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")

config = load_config()
selector = MicrophoneSelector(config.whisper_sample_rate)
mics = selector.list_microphones()
for item in mics:
    print(f"[{item.display}] {item.name}")
choice = int(input("\nChoose microphone: "))
device = selector.resolve_device(choice)

recognizer = sr.Recognizer()

print("\nSpeak a Telugu Bible reference (e.g. 'కీర్తనలు 25 14')")
print("Press Ctrl+C after you speak...\n")

try:
    with VoiceSegmentStream(config, device=device) as stream:
        for audio, start_time, end_time in stream.iter_segments():
            print(f"\nCaptured {len(audio)/16000:.2f}s of audio")

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav_path = f.name
                with wave.open(f, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes((audio * 32767).astype(np.int16).tobytes())

            with sr.AudioFile(wav_path) as source:
                sr_audio = recognizer.record(source)

            try:
                google_result = recognizer.recognize_google(sr_audio, language="te-IN")
                print(f"Google (Telugu): {google_result}")
            except sr.UnknownValueError:
                print("Google (Telugu): Could not understand audio")
            except sr.RequestError as e:
                print(f"Google (Telugu) error: {e}")

            try:
                google_en = recognizer.recognize_google(sr_audio, language="en-US")
                print(f"Google (English): {google_en}")
            except sr.UnknownValueError:
                print("Google (English): Could not understand audio")
            except sr.RequestError as e:
                print(f"Google (English) error: {e}")
            break
except KeyboardInterrupt:
    print("\nStopped")
