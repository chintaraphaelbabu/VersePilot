# Voice Bible

Voice Bible listens to a microphone, transcribes speech locally with Faster-Whisper, detects spoken intent, parses Bible references in English or Telugu, manages sermon context, and automatically displays them in FreeShow using its official REST API.

## Features

- **Intent Detection**: Classifies speech into `REFERENCE`, `NAVIGATION`, `CROSS_REFERENCE`, or `IGNORE` to eliminate false positives. The parser runs ONLY for valid actions.
- **Low-Latency VAD & Whisper Pipeline**: Highly optimized speech detection to send verses as fast as possible.
- **Sermon Context State Machine**: 
  - Tracks a **Primary** passage (the main scripture being preached).
  - Supports temporary **Cross References** without losing track of the primary passage.
  - History stack to go back to previous scriptures.
- **Voice Commands**:
  - `next verse` / `previous verse`
  - `next chapter` / `previous chapter`
  - `verse [number]` (e.g., *verse five*) / `chapter [number]` (e.g., *chapter four*)
  - `go back` (traverse history)
  - `return to passage` / `go back to passage`
  - `continue` / `continue reading` (advances the primary passage)
- **Configurable Whisper Latency Modes**:
  - `FAST`: Uses the `small` model with `beam_size = 1`.
  - `BALANCED`: Uses the `small` model with `beam_size = 3`.
  - `ACCURATE`: Uses the `medium` model with `beam_size = 5`.

---

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

### 1. List Microphones
Identify the index of your preferred input device:

```bash
python main.py --list-mics
```

### 2. Start the Application
Run the listener using your microphone index (e.g., `--mic 1`) and latency profile (e.g., `--mode FAST`):

```bash
python main.py --mic 1 --mode FAST
```

To watch every recognition stage in a local desktop window:

```bash
python main.py --gui --mic 3 --language TELUGU --mode FAST
```

The monitor shows the raw transcription, corrected text, detected intent, partial reference-builder state, candidate scores, and the diagnostic log. Use the **Stop listener** button to end the listener.

### 3. Train from sermon recordings
Download sermon audio with `sermon_files\download.bat`, or place `.mp3`, `.wav`, `.flac`, or `.m4a` files in `sermon_files\video\`. Then run:

```bash
python replay.py --dataset sermon_files/video --language telugu
python learning_pipeline.py
```

Generated replay reports are stored in `outputs\replay\`; learning suggestions are stored in `outputs\learning\`. Maintenance scripts are in `scripts\maintenance\`.

## Project structure

- `src\versepilot\` - application package and Bible data
- `scripts\` - replay, learning, and maintenance commands
- `tests\` - regression tests
- `sermon_files\video\` - downloaded sermon audio
- `outputs\` - generated replay and learning reports

Audio stays on this computer while the application is running. Faster-Whisper may download a model once if it is not already cached; after that, live transcription and replay run locally. Training reports use downloaded sermon recordings but do not fine-tune the Whisper model.

---

## Configuration

You can configure the application using environment variables:

| Environment Variable | Description | Default |
|----------------------|-------------|---------|
| `VERSE_WHISPER_MODE` | Whisper latency mode (`FAST`, `BALANCED`, `ACCURATE`). | `BALANCED` |
| `VERSE_WHISPER_MODEL_NAME` | Explicitly overrides the Whisper model size (`small`, `medium`, etc.). | *(Derived from mode)* |
| `VERSE_DEVICE` | Hardware device for Whisper execution (`cpu` or `cuda`). | `cpu` |
| `VERSE_LANGUAGE` | Language restriction (`en`, `te`, or `None` for auto-detect). | `None` |
| `FREESHOW_HOST` | Host IP address of the FreeShow REST API. | `127.0.0.1` |
| `FREESHOW_PORT` | Port of the FreeShow REST API. | `5506` |

---

## How It Works

```
Microphone → VoiceSegmentStream (VAD) → Whisper → IntentDetector → BibleReference Parser → SermonContext → Background FreeShow Thread (REST Post)
```

- **VAD (Voice Activity Detection)**: Segments audio in real-time, detecting speech start and end with minimal delay.
- **IntentDetector**: Pre-filters speech completely offline using keyword and regex classification. Ignores unrelated sermon speech to prevent live slide changes.
- **SermonContext**: Handles logic for primary vs cross-references, commands, and history.
- **Async REST Poster**: Sends JSON payload `{ "action": "start_scripture", "reference": "BOOK_ID.CHAPTER.VERSE" }` on a separate thread to keep the voice loop completely non-blocking.