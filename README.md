# Terminal soundscape

A collection of real-world sounds for terminal simulations. The current inventory contains one crane substitute candidate; it has not been listened to and is not release-ready. Research and blockers are recorded for [cranes](docs/research-crane.md), [container contact](docs/research-contact.md), [vehicles](docs/research-vehicle.md), [warnings](docs/research-warnings.md), and [reefer and harbour ambience](docs/research-ambience.md). No licence applies to the collection as a whole; check each item's terms, particularly non-commercial and share-alike restrictions.

## Browser delivery

Run `python soundscape.py catalogue` after validating or changing the inventory. It validates the masters and generates [browser.json](browser.json), [CATALOGUE.md](CATALOGUE.md), [ATTRIBUTION.md](ATTRIBUTION.md), and [COVERAGE.md](COVERAGE.md). The mapping includes pending assets for inspection, not as an assertion of release readiness. Filter `review_status` for `reviewed`, and check per-item `commercial_use`, `share_alike`, attribution and licence before shipping. An empty mapping means no sounds are available. The coverage report lists each priority category using explicit contributor classifications and reviewed status; assess suitability before use.

Serve the repository over HTTP, fetch `browser.json`, and resolve each `path` relative to that file. The 48 kHz 16-bit PCM WAV masters are the browser delivery files; browsers can decode them with Web Audio's `decodeAudioData` or play them with an audio element. Respect browser autoplay rules by starting audio after a user gesture. Use the event and playback fields to select an asset: one-shots and full events play once; loop only recordings reviewed at their boundaries. Follow each asset's playback guidance. Use mono sources with a Web Audio `PannerNode` (or Three.js positional audio) for point sources, and stereo ambience without positional panning. Start with conservative gain and distance attenuation, then tune against the scene scale and real equipment; no universal distances are asserted. Avoid stacking an unbounded number of simultaneous sounds.

## Setup and commands

Python 3.9+ is required; the current commands use only the standard library. Run from the repository root on Windows or Linux:

```sh
python -m unittest discover -s tests -v
python soundscape.py inspect path/to/prepared.wav
python soundscape.py import path/to/prepared.wav path/to/metadata.json --original-source path/to/original --dry-run
python soundscape.py import path/to/prepared.wav path/to/metadata.json --original-source path/to/original
python soundscape.py validate
python soundscape.py catalogue --dry-run
python soundscape.py catalogue --overwrite
```

Use `--root PATH` on import, validate and catalogue to operate on another collection. Import refuses an existing ID or destination; dry runs do not write. Catalogue validates before regenerating the four files above. Existing reports are protected unless `--overwrite` is supplied; review or back them up before replacing them. Use only trusted local files; do not execute source downloads. The WAV reader checks 16-bit PCM, 48 kHz, mono/stereo, non-silence, and clipping at full scale. A passing check is not a listening review. `inspect` accepts other PCM sample rates for diagnosis. No conversion is implemented: prepare WAVs separately with a trusted tool such as FFmpeg, record exact commands and hashes in metadata, and preserve the source separately. Pass the original downloaded file with `--original-source`; its hash is recorded as `source_sha256`, while `sha256` identifies the prepared WAV. If the WAV is unchanged, pass it for both paths.

## Contribution and review

Prepare a UTF-8 JSON object with all fields below. All values must be nonempty strings. Licence identifiers accepted are `CC0-1.0`, `CC-BY-4.0`, `CC-BY-SA-4.0`, `CC-BY-NC-4.0`, and `CC-BY-NC-SA-4.0`; no-derivatives and ambiguous permissions are excluded. Verify the item page and permissions yourself: the software cannot establish that assertions are true. Credit authors even for CC0 when known. Include the exact processing command in `processing`; use `none` for an unchanged source. Distinguish derivatives from independent recordings in the description and processing. Do not call a recording reviewed until a person or capable agent has listened, including loop boundaries where applicable. Use `pending` and describe the blocker until then.

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

Optionally set `priority_category` to one of `crane movement`, `container contact`, `carrier or tractor movement`, `terminal warnings`, `reefer ambience`, or `harbour ambience`. Coverage counts only explicitly classified reviewed recordings, so an unclassified recording does not close a gap. Playback values are `one-shot`, `full-event`, or `loop`; review status is `pending` or `reviewed`. A loop requires a real boundary listening review before release. Use mono for appropriate spatial point sources and stereo for ambience; do not infer a particular terminal machine from sound alone. The metadata is a human assertion, not a rights or authenticity guarantee. The catalogue flags pending entries; consumers must check review status and suitability before use.
