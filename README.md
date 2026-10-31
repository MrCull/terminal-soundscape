# Terminal Soundscape

An independently usable, traceable collection of real terminal and port audio for browser simulations. The inventory is early: one crane recording is present as an unauditioned candidate. It is **not release-ready**; no other category currently has audio.

## Maintainer commands

Requires Python 3.10+. From the repository root:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: . .venv/bin/activate
python -m pip install -e .
soundscape validate manifest.json
soundscape catalogue manifest.json --dry-run
soundscape catalogue manifest.json --output CATALOGUE.md
```

Catalogue generation refuses to overwrite an existing output. Validation checks required manifest fields, unique IDs, collection-contained paths, file presence, SHA-256, and WAV properties when media is WAV. OGG/other decoding and clipping analysis are not implemented yet. Run local checks with `python -m unittest discover -s tests -v`.

## Rights and review

Each accepted entry needs item-level evidence that redistribution is permitted, exact licence and attribution, commercial-use status, provenance and source/output hashes. Do not infer rights from a site-wide statement. Keep non-commercial and share-alike obligations conspicuous. Unknown rights are not eligible for the library. Candidates remain in `assets/candidates/` and must not be treated as release-ready. A named listener must record an actual audition and loop-boundary review before status can become `release_ready`.

See [docs/collection-status.md](docs/collection-status.md) for current inventory, candidate provenance, gaps, and remaining work.
