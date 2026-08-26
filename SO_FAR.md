# VersePilot: So Far

This file records completed features and how they were applied.

## Completed

### Project organization
- Moved application code into `src/versepilot/`.
- Grouped commands under `scripts/` and maintenance tools under `scripts/maintenance/`.
- Grouped tests under `tests/`, static data under `data/`, sermon audio under `sermon_files/video/`, and generated reports under `outputs/`.
- Preserved root launch commands with compatibility wrappers.

### Local transcription
- Replaced the default Google Speech-to-Text path with local Faster-Whisper.
- Added local CPU/CUDA model selection and cached model loading.
- Set the accurate profile to use `large-v3` for difficult church livestream audio.

### Audio cleanup
- Added DC offset removal, low-frequency rumble filtering, conservative noise suppression, and peak control before transcription.

### Reference processing
- Added correction and reference-building logic for English and Telugu book names, number words, chapters, verses, and ranges.
- Added candidate scoring and Bible text matching against the local Telugu Bible database.

### FreeShow integration
- Sends resolved references to FreeShow asynchronously through its local REST endpoint.

### Continuous local Whisper context
- Passes a bounded rolling prompt from recent recognized speech into the next local Whisper call.
- Uses deterministic decoding and no-speech/compression filters for steadier livestream transcription.
- Clears the prompt after prolonged silence so a new sermon section starts cleanly.
- Validated with compilation, all 5 regression tests, and a focused context-reset check.

### Live diagnostics GUI
- Added a local GUI monitor showing raw speech, corrected text, intent, builder state, candidate decisions, confidence, and diagnostics.

## In Progress

### YouTube-style local captions
- Add stabilized live caption text in the GUI.
- Add reference-aware confirmation so uncertain numbers are held before sending.
