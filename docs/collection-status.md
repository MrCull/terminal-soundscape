# Collection status

Checked 2026-10-31. Current audio inventory: 6 original candidates, 0 release-ready assets, and 6 mechanically browser-compatible MP3 previews. The audio originals total 982.397 seconds (16m 22s) by `ffprobe`; no original or derivative has been auditioned. The previews are not release-ready and do not have event mappings. One additional 187.462-second video candidate is tracked separately below.

The MP3 previews are in `assets/browser-candidates/`. `preview-manifest.json` records source and output hashes, licensing and attribution, technical inspection, and conversion details. The conversion uses FFmpeg `libmp3lame` at 192 kbit/s, strips metadata, and applies no normalization or fades. Their durations may differ slightly from source due to MP3 encoder padding. Listen to each preview and review any selected event/loop before approving it.

## Candidate

`mobile-harbour-crane-candidate-01` is a 48.548-second stereo Ogg recording at 96 kHz. The [Wikimedia Commons file page](https://commons.wikimedia.org/wiki/File:WWS_Mobileharbourcrane.ogg) identifies a Gottwald HMK7408B mobile cargo handling crane at Port of Rauma, recorded by Teemu Ahola, and documents CC BY 4.0, including redistribution and adaptation rights with attribution. That licence allows commercial use. It is an authentic crane-operation recording, but no narrower event/segment identity is claimed. The file is stored as downloaded, without conversion or other processing. Its SHA-256 is recorded in `manifest.json`.

**Review blocker:** this environment cannot listen to the recording. No listening or loop-boundary review is claimed. The candidate must be auditioned before it can satisfy the release-ready crane requirement. Because the supplied recording is stereo and 96 kHz, any later mono/48 kHz derivative needs an explicit processing record and review.

## Additional candidates

- `container-gantry-crane-candidate-01`: Teemu Ahola / Work With Sounds / Werstas, a real gantry crane loading M/S Sandy Rickmers at Port of Rauma. The [Commons file page](https://commons.wikimedia.org/wiki/File:WWS_Containershipgantrycrane.ogg) documents CC BY 4.0 and an explicit creator permission record. 126.869 seconds, stereo Ogg at 96 kHz. Authentic container-terminal equipment; event segments remain unreviewed.
- `rotterdam-harbour-ambience-candidate-01`: Robin Koek's [Rotterdam harbour area recording](https://commons.wikimedia.org/wiki/File:Algemene_sfeer_van_het_havengebied_Rotterdam_-_SoundCloud_-_GvNL-Steim_Workshop.ogg), described as water, birds and distant harbour activity. 95.945 seconds, stereo Ogg at 44.1 kHz. CC BY 3.0. No loop claim is made.
- `container-ship-arrival-candidate-01`: Klankbeeld / Beeld en Geluid's [container ship arrival recording](https://commons.wikimedia.org/wiki/File:Containerschip_meert_aan_in_haven_-_SoundCloud_-_Beeld_en_Geluid.ogg). 430.348 seconds, stereo Ogg at 48 kHz. CC BY-SA 3.0: redistribution is allowed, and adaptations must retain the same or a compatible licence. The source describes a ship arriving and crane unloading; details are unauditioned.
- `dortmund-container-terminal-candidate-01`: Konrad Gutkowski and Jonathan Nicolai / Work With Sounds' [Port of Dortmund terminal recording](https://commons.wikimedia.org/wiki/File:WWS_ContainerTerminalatthePortofDortmund.ogg). The item page describes container transport by three gantry cranes and acoustic start signals, and documents CC BY 4.0 plus recorded permission. 189.595 seconds, stereo Ogg at 44.1 kHz. Candidate for terminal ambience, container handling and warning research; no narrower event is claimed without listening.
- `container-reach-stacker-candidate-01`: Teemu Ahola / Work With Sounds / Werstas' [reach stackers at Port of Rauma](https://commons.wikimedia.org/wiki/File:WWS_Containerreachstackers.ogg). The item page identifies Kone Cranes SMV 4531 TB5 equipment loading/unloading trucks and documents CC BY 4.0 with recorded permission. 91.091 seconds, stereo Ogg at 96 kHz. It is directly relevant carrier movement, pending listening review.

## Video reference

`assets/candidates/videos/Container_reach_stacker_Port_of_Rauma.webm` is a 187.462-second 1080p WebM clip showing a Kone Cranes SMV 4531 TB5 reach stacker loading/unloading trucks at Port of Rauma. It contains stereo Vorbis audio at 44.1 kHz. The [Commons page](https://commons.wikimedia.org/wiki/File:Container_reach_stacker,_Port_of_Rauma.webm) identifies Work With Sounds, sound recordist Teemu Ahola and video recordist Leena Ahonen, and verifies CC BY 3.0. File SHA-256: `291bc79eb9f08b0ca509e12e2be3ced09d619d6ac5ad96a35ccb4d6e5c1f3050`. This is an actual video source, not a browser-ready audio asset; no audio extraction, use, or listening review is claimed.

All six audio files have source-page rights records, attribution and hashes in `manifest.json`. Their commercial-use status is allowed under the listed licences; one carries share-alike obligations. They remain candidates pending actual listening review.

## Coverage and remaining work

| Category | Status | Remaining work |
| --- | --- | --- |
| Crane hoist/movement | Two authentic rights-documented audio candidates; unauditioned | Human listening, identify useful event/segment, check quality and boundaries, process only if useful, review derivative |
| Container contact/placement | Terminal field recordings contain handling as candidate soundscapes; no isolated contact event | Listen, identify whether usable contact/placement is present; otherwise source a distinct event |
| Carrier/tractor movement | One authentic reach stacker audio candidate and one supporting video; unauditioned | Listen; identify useful movement events; prepare reviewed browser formats |
| Terminal warnings | One terminal soundscape source page describes acoustic crane start signals; recording unauditioned | Verify audible signal, research operating context, identify event and review |
| Reefer ambience | No asset | Source and verify; listen; determine channel and honest loop guidance |
| Harbour ambience | One rights-documented candidate; unauditioned | Listen; determine channel and honest loop guidance |
| Browser delivery | MP3 preview files and generated rights/coverage/candidate mapping reports exist; none are reviewed or event-mapped | Human listen to previews; map only confirmed events; document browser integration guidance |

No source or listening blockers are fabricated for categories without candidates. Counts and duration refer to all six audio candidates above; they must not be interpreted as release-ready coverage achieved. Licence statuses are per item as recorded in `manifest.json`, including the share-alike obligation on the container-ship arrival recording.
