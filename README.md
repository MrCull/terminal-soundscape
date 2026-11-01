# Terminal Soundscape

An independently usable, traceable collection of real terminal and port audio for browser simulations. The inventory contains 106 unauditioned audio candidates and six browser-compatible MP3 previews. There are no release-ready assets or validated event mappings yet. The 100 additions are source-documented port and harbour field recordings. Eight source descriptions mention cargo, terminal, or vessel operations; the other 92 are port and harbour soundscapes. All remain unauditioned.

## Maintainer commands

Requires Python 3.10+. From the repository root:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: . .venv/bin/activate
python -m pip install -e .
soundscape validate manifest.json
soundscape inspect assets/candidates/WWS_Mobileharbourcrane.ogg
soundscape import path/to/recording.wav assets/candidates/new-recording.wav --dry-run
soundscape import path/to/recording.wav assets/candidates/new-recording.wav
soundscape catalogue manifest.json --dry-run
soundscape catalogue manifest.json --output CATALOGUE.md
soundscape reports manifest.json --dry-run
soundscape reports manifest.json --output-dir docs/generated
soundscape browser-prepare manifest.json --dry-run
soundscape browser-prepare manifest.json
```

Catalogue and report generation refuse to overwrite existing output. `import` only copies a local file beneath the collection root, rejects path escapes, and never overwrites. `inspect` reports file size and SHA-256, and uses FFprobe when installed for media properties (WAV has a Python standard-library fallback). Validation checks required manifest fields, unique IDs, collection-contained paths, file presence, hashes, file sizes, WAV properties, FFmpeg decoding/signal, rights metadata and the listener/loop-review gate for release-ready items. `reports` generates attribution, coverage and explicitly provisional event-mapping files. `browser-prepare` writes 192 kbit/s MP3 previews with a separate processing/provenance manifest; these are browser-compatible but remain unreviewed previews, not release assets. It never overwrites output. Run local checks with `python -m unittest discover -s tests -v`.

## Rights and review

Each accepted entry needs item-level evidence that redistribution is permitted, exact licence and attribution, commercial-use status, provenance and source/output hashes. Do not infer rights from a site-wide statement. Keep non-commercial and share-alike obligations conspicuous. Unknown rights are not eligible for the library. Candidates remain in `assets/candidates/` and must not be treated as release-ready. A named listener must record an actual audition and loop-boundary review before status can become `release_ready`.

See [docs/collection-status.md](docs/collection-status.md) for current inventory and gaps, and [docs/research-log.md](docs/research-log.md) for source decisions and operating-context research.

Generated reports currently live in [`docs/generated/`](docs/generated/): catalogue, attribution, coverage, and provisional candidate mapping. Rebuild catalogue with the `catalogue` command; rebuild the other reports with `reports`. The [audio file inventory](docs/audio-file-inventory.md) lists every master and preview with a source-based description and probed media details.


## Repository layout

- `src/soundscape/` and `tests/` contain the current Python package and its tests.
- `assets/candidates/` stores source audio candidates; `assets/browser-candidates/` stores unreviewed MP3 previews.
- `manifest.json` is the current inventory. `docs/` contains collection guidance, research, status, and current generated reports.
- `first-collection/` keeps the earlier 18-recording WAV collection self-contained, including its own manifest, validation tool, reports, research, tests, and separate MP3 previews. Start with [`first-collection/docs/README.md`](first-collection/docs/README.md).
- [`tools/audio-audition/`](tools/audio-audition/README.md) provides a local browser player and human listening-note export for both collections.
- [`tools/audio-tagging/`](tools/audio-tagging/README.md) runs local YAMNet sound-event tagging across all masters; its automated suggestions are separate from listening review.

The two collections use different manifest schemas. The first collection's script defaults to `first-collection/manifest.json` and writes reports inside `first-collection/`; its WAV files remain under `first-collection/audio/`.
