# Offline sound-event tagging

This optional tool uses Google's YAMNet AudioSet classifier through LiteRT to produce broad sound-event tags for the 124 master recordings. It processes the audio locally; recordings are not uploaded. The model can suggest categories such as vehicle, engine, water, bird, speech, or machinery. Scores are clues for triage, not captions, proof of a sound's identity, or listening approval.

Install the optional runtime and run it from the repository root:

```sh
python -m pip install -r tools/audio-tagging/requirements.txt
python tools/audio-tagging/tag_audio.py
```

On first run, the script downloads the Apache-2.0 YAMNet TFLite model and class labels from the pinned Hugging Face revision into `~/.cache/terminal-soundscape/yamnet/`. It checks both downloaded files against pinned SHA-256 values. FFmpeg decodes each master to mono 16 kHz float audio in a pipe; the model scans each file in five-second windows. No source audio is edited. Results are written to `docs/generated/audio-event-tags.json` and `docs/audio-event-tags.md`.

Use `--overwrite` to replace previous reports. Use `--model-dir PATH` to use an existing model cache or `--output-json PATH --output-md PATH` to choose report locations. `--threads N` controls CPU inference threads.

YAMNet was trained on AudioSet's broad labels. It can confuse similar sounds, miss events, or assign generic labels; review the highlighted times in a player before using a tag as a factual description. It cannot establish licensing, authenticity, recording quality, loop suitability, or release readiness.
