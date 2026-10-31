# Terminal Soundscape

An independently usable, traceable collection of real terminal and port audio for browser simulations. The inventory currently contains five unauditioned audio candidates and one video reference. There are no release-ready or browser-ready files yet.

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
```

Catalogue generation refuses to overwrite an existing output. `import` only copies a local file beneath the collection root, rejects path escapes, and never overwrites. `inspect` reports file size and SHA-256, and uses FFprobe when installed for media properties (WAV has a Python standard-library fallback). Validation checks required manifest fields, unique IDs, collection-contained paths, file presence, SHA-256, WAV properties, rights metadata and the listener gate for release-ready items. OGG/other decoding validation and clipping analysis are not implemented yet. Run local checks with `python -m unittest discover -s tests -v`.

## Rights and review

Each accepted entry needs item-level evidence that redistribution is permitted, exact licence and attribution, commercial-use status, provenance and source/output hashes. Do not infer rights from a site-wide statement. Keep non-commercial and share-alike obligations conspicuous. Unknown rights are not eligible for the library. Candidates remain in `assets/candidates/` and must not be treated as release-ready. A named listener must record an actual audition and loop-boundary review before status can become `release_ready`.

See [docs/collection-status.md](docs/collection-status.md) for current inventory, candidate provenance, gaps, and remaining work.
