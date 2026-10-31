# Terminal soundscape

A collection of real-world sounds for terminal simulations. The current inventory is **empty**: no recordings are reviewed or release-ready. See [research](docs/research-crane.md) for the first candidate and the listening blocker. No licence applies to the collection as a whole; check each item's terms, particularly non-commercial and share-alike restrictions.

## Setup and commands

Python 3.9+ is required; the current commands use only the standard library. Run from the repository root on Windows or Linux:

```sh
python -m unittest discover -s tests -v
python soundscape.py inspect path/to/prepared.wav
python soundscape.py import path/to/prepared.wav path/to/metadata.json --dry-run
python soundscape.py import path/to/prepared.wav path/to/metadata.json
python soundscape.py validate
python soundscape.py catalogue --dry-run
python soundscape.py catalogue
```

Use `--root PATH` on import, validate and catalogue to operate on another collection. Import refuses an existing ID or destination; dry runs do not write. Catalogue validates before writing and regenerates `CATALOGUE.md`. Back up existing reports before regeneration. Use only trusted local files; do not execute source downloads. The WAV reader checks 16-bit PCM, 48 kHz, mono/stereo, non-silence, and clipping at full scale. A passing check is not a listening review. `inspect` accepts other PCM sample rates for diagnosis. No conversion is implemented: prepare WAVs separately with a trusted tool such as FFmpeg, record exact commands and hashes in metadata, and preserve the source separately. Import records the hash of the supplied prepared WAV as both `source_sha256` and `sha256`; original download hashes must be recorded in `processing` until the manifest supports a separate original-source field.

## Contribution and review

Prepare a UTF-8 JSON object with all fields below. All values must be nonempty strings. Licence identifiers accepted are `CC0-1.0`, `CC-BY-4.0`, `CC-BY-SA-4.0`, `CC-BY-NC-4.0`, and `CC-BY-NC-SA-4.0`; no-derivatives and ambiguous permissions are excluded. Verify the item page and permissions yourself: the software cannot establish that assertions are true. Credit authors even for CC0 when known. Include original source hash and exact processing command in `processing`; use `none` for an unchanged source. Distinguish derivatives from independent recordings in the description and processing. Do not call a recording reviewed until a person or capable agent has listened, including loop boundaries where applicable. Use `pending` and describe the blocker until then.

```json
{
  "id": "crane-example", "description": "Bridge crane movement",
  "source_url": "https://example.org/item", "creator": "Recorder",
  "license": "CC-BY-4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
  "rights_evidence_url": "https://example.org/item", "rights_verified_date": "2026-10-31",
  "attribution": "Recorder, Bridge crane movement, CC BY 4.0; modified",
  "authenticity": "substitute", "authenticity_evidence": "Source describes a bridge crane, not a container crane",
  "event": "crane movement", "playback": "full-event", "playback_guidance": "Play once at the machine",
  "processing": "Original SHA-256 and exact conversion command here", "quality_notes": "Source fidelity and noise here",
  "review_status": "pending", "reviewer": "none", "review_notes": "Listening pending"
}
```

Playback values are `one-shot`, `full-event`, or `loop`; review status is `pending` or `reviewed`. A loop requires a real boundary listening review before release. Use mono for appropriate spatial point sources and stereo for ambience; do not infer a particular terminal machine from sound alone. The metadata is a human assertion, not a rights or authenticity guarantee. The catalogue flags pending entries; consumers must check review status and suitability before use.
