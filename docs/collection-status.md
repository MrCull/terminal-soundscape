# Collection status

Checked 2026-10-31. Current audio inventory: 106 original candidates, 0 release-ready assets, and 6 mechanically browser-compatible MP3 previews. The full originals total 22,286.852 seconds (6h 11m 26s) by `ffprobe`; no original or derivative has been auditioned. The previews are not release-ready and do not have event mappings.

The MP3 previews are in `assets/browser-candidates/`. `preview-manifest.json` records source and output hashes, licensing and attribution, technical inspection, and conversion details. The conversion uses FFmpeg `libmp3lame` at 192 kbit/s, strips metadata, and applies no normalization or fades. Their durations may differ slightly from source due to MP3 encoder padding. Listen to each preview and review any selected event/loop before approving it.

## Original port and terminal candidates

`mobile-harbour-crane-candidate-01` is a 48.548-second stereo Ogg recording at 96 kHz. The [Wikimedia Commons file page](https://commons.wikimedia.org/wiki/File:WWS_Mobileharbourcrane.ogg) identifies a Gottwald HMK7408B mobile cargo handling crane at Port of Rauma, recorded by Teemu Ahola, and documents CC BY 4.0, including redistribution and adaptation rights with attribution. That licence allows commercial use. It is an authentic crane-operation recording, but no narrower event/segment identity is claimed. The file is stored as downloaded, without conversion or other processing. Its SHA-256 is recorded in `manifest.json`.

**Review blocker:** this environment cannot listen to the recording. No listening or loop-boundary review is claimed. The candidate must be auditioned before it can satisfy the release-ready crane requirement. Because the supplied recording is stereo and 96 kHz, any later mono/48 kHz derivative needs an explicit processing record and review.

## Additional candidates

- `container-gantry-crane-candidate-01`: Teemu Ahola / Work With Sounds / Werstas, a real gantry crane loading M/S Sandy Rickmers at Port of Rauma. The [Commons file page](https://commons.wikimedia.org/wiki/File:WWS_Containershipgantrycrane.ogg) documents CC BY 4.0 and an explicit creator permission record. 126.869 seconds, stereo Ogg at 96 kHz. Authentic container-terminal equipment; event segments remain unreviewed.
- `rotterdam-harbour-ambience-candidate-01`: Robin Koek's [Rotterdam harbour area recording](https://commons.wikimedia.org/wiki/File:Algemene_sfeer_van_het_havengebied_Rotterdam_-_SoundCloud_-_GvNL-Steim_Workshop.ogg), described as water, birds and distant harbour activity. 95.945 seconds, stereo Ogg at 44.1 kHz. CC BY 3.0. No loop claim is made.
- `container-ship-arrival-candidate-01`: Klankbeeld / Beeld en Geluid's [container ship arrival recording](https://commons.wikimedia.org/wiki/File:Containerschip_meert_aan_in_haven_-_SoundCloud_-_Beeld_en_Geluid.ogg). 430.348 seconds, stereo Ogg at 48 kHz. CC BY-SA 3.0: redistribution is allowed, and adaptations must retain the same or a compatible licence. The source describes a ship arriving and crane unloading; details are unauditioned.
- `dortmund-container-terminal-candidate-01`: Konrad Gutkowski and Jonathan Nicolai / Work With Sounds' [Port of Dortmund terminal recording](https://commons.wikimedia.org/wiki/File:WWS_ContainerTerminalatthePortofDortmund.ogg). The item page describes container transport by three gantry cranes and acoustic start signals, and documents CC BY 4.0 plus recorded permission. 189.595 seconds, stereo Ogg at 44.1 kHz. Candidate for terminal ambience, container handling and warning research; no narrower event is claimed without listening.
- `container-reach-stacker-candidate-01`: Teemu Ahola / Work With Sounds / Werstas' [reach stackers at Port of Rauma](https://commons.wikimedia.org/wiki/File:WWS_Containerreachstackers.ogg). The item page identifies Kone Cranes SMV 4531 TB5 equipment loading/unloading trucks and documents CC BY 4.0 with recorded permission. 91.091 seconds, stereo Ogg at 96 kHz. It is directly relevant carrier movement, pending listening review.

The six original port-relevant audio files have source-page rights records, attribution and hashes in `manifest.json`. Their commercial-use status is allowed under the listed licences; one carries share-alike obligations. They remain candidates pending actual listening review.

## Additional port and harbour candidates

This branch adds 100 playable field recordings whose item pages identify a port, harbour, pier, or vessel operating there. All 100 are Aporee recordings hosted by the Internet Archive, and each item's metadata states CC BY 3.0. The manifest records each source page, creator/uploader, item-level licence, original-file SHA-256, size, codec, channels, sample rate and duration.

Eight source descriptions mention cargo, terminal, or vessel operations. The other 92 are general port or harbour soundscapes, including fishing harbours. These are port-context recordings, not 100 isolated terminal-equipment events. All remain unauditioned candidates, have no prepared derivatives and are not release-ready.

## Coverage and remaining work

| Category | Status | Remaining work |
| --- | --- | --- |
| Crane hoist/movement | Two authentic rights-documented audio candidates; unauditioned | Human listening, identify useful event/segment, check quality and boundaries, process only if useful, review derivative |
| Container contact/placement | Terminal field recordings contain handling as candidate soundscapes; no isolated contact event | Listen, identify whether usable contact/placement is present; otherwise source a distinct event |
| Carrier/tractor movement | One authentic reach stacker audio candidate; unauditioned | Listen; identify useful movement events; prepare reviewed browser formats |
| Terminal warnings | One terminal soundscape source page describes acoustic crane start signals; recording unauditioned | Verify audible signal, research operating context, identify event and review |
| Reefer ambience | No asset | Source and verify; listen; determine channel and honest loop guidance |
| Port/harbour soundscapes | 92 new port/harbour-context recordings plus the earlier Rotterdam harbour candidate; all unauditioned | Listen; assess ambience and loop boundaries; do not assign equipment events without evidence |
| Terminal/cargo port candidates | Eight added source descriptions mention cargo, terminal, ferry or vessel operations; all unauditioned | Listen; confirm which are useful and identify the actual audible event before event mapping |
| Browser delivery | Six MP3 preview files and generated rights/coverage/candidate mapping reports exist; none are reviewed or event-mapped | Human listen to previews; map only confirmed events; document browser integration guidance |

No source or listening blockers are fabricated for categories without candidates. Counts and duration refer to all 106 manifest candidates, including the 100 port and harbour recordings; they must not be interpreted as release-ready coverage achieved. Licence statuses are per item as recorded in `manifest.json`, including the share-alike obligation on the container-ship arrival recording.
