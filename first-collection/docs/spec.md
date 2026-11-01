# First terminal sound collection

## Problem Statement

Developers of container simulations need convincing real-world audio that can be redistributed with their software. Finding, evaluating, processing and crediting suitable recordings is time-consuming, and recordings with different licence restrictions cannot safely be treated as one unrestricted collection. There is not yet a usable collection in this repository.

## Solution

Build and populate a first vertical slice of a reusable terminal audio library. Deliver playable recordings, traceable rights and processing information, practical maintenance tools, and guidance for event-driven browser simulations. Shipping Container Sims and the professional terminal simulation are the first intended audiences; the library should remain useful independently of either. Continue expanding the catalogue after the first slice.

## User Stories

1. As a simulation developer, I want actual playable audio in the repository, so that I can use the collection without sourcing each file myself.
2. As a simulation developer, I want authentic crane hoist and movement recordings, so that crane operations sound convincing.
3. As a simulation developer, I want container contact and placement sounds, so that handling events have useful audible feedback.
4. As a simulation developer, I want carrier or tractor movement sounds, so that terminal vehicles can be heard.
5. As a simulation developer, I want appropriate warning sounds, so that I can represent alarms where they actually apply.
6. As a simulation developer, I want reefer and harbour ambience, so that scenes have environmental context.
7. As a simulation developer, I want meaningful sound variations, so that repeated events do not sound identical.
8. As a simulation developer, I want one-shots, loops and full events identified, so that I can select suitable playback behaviour.
9. As a browser developer, I want browser-ready audio and event mappings, so that another agent can integrate the sounds later.
10. As a developer, I want point-source and ambience channel choices documented, so that I can use spatial audio appropriately.
11. As a developer, I want realistic guidance on alarms and attenuation, so that sounds match operating conditions.
12. As a developer, I want authentic recordings distinguished from substitutes and composites, so that I understand what I am using.
13. As a developer, I want uncertainty about equipment identity recorded, so that a plausible sound is not mistaken for a verified recording.
14. As a user, I want each recording to be free to obtain and redistribute, so that I do not need to purchase assets.
15. As a user, I want the licence and attribution for each recording, so that I can comply with its terms.
16. As a future commercial user, I want commercial-use restrictions clearly marked and filterable, so that I can identify assets suitable for my use.
17. As a user, I want share-alike obligations visible, so that I can assess their effect on my distribution.
18. As a maintainer, I want item-specific evidence of redistribution rights, so that ambiguous or prohibited recordings are excluded.
19. As a maintainer, I want a research log of candidates and rejections, so that future searches build on prior work.
20. As a maintainer, I want sources requiring free accounts recorded when inaccessible, so that manual acquisition can be considered later.
21. As a maintainer, I want source hashes, derivatives and processing history, so that every asset is traceable.
22. As a maintainer, I want listened-to recordings and loop boundaries reviewed, so that technical validity is not mistaken for audio quality.
23. As a maintainer, I want listening limitations reported, so that unauditioned files are not represented as release-ready.
24. As a maintainer, I want safe import, inspection and validation commands, so that new recordings can be added consistently.
25. As a maintainer, I want a generated catalogue, attribution and coverage report, so that documentation reflects the actual inventory.
26. As a maintainer, I want coverage gaps and candidate restrictions documented, so that I can prioritise further collection.
27. As a contributor on Windows or Linux, I want documented dependencies and commands, so that I can reproduce the workflow.
28. As a user, I want files checked for decoding, signal, clipping and promised format, so that broken assets are caught early.

## Implementation Decisions

- Prioritise a working first slice: crane hoist and movement, container contact and placement, carrier or tractor movement, a realistic warning, reefer and harbour ambience. Aim for at least one useful, reviewed recording in each where legally and practically available. Report gaps rather than inventing assets. Expand toward the brief's broader equipment checklist and meaningful variants later.
- All sources must be real recordings, not generated or synthesised audio. Legitimate processing must be recorded and retain realism. Do not use Terminal Twin audio or inspect that repository for this work. Existing audio elsewhere is only a candidate after item-level provenance and rights review.
- Store playable audio in this repository. Default masters to 48 kHz, 16-bit PCM WAV, using mono for suitable point sources and stereo for ambience. Provide a documented browser-ready delivery format as needed. Preserve provenance and flag limited source fidelity.
- Accept only recordings free to obtain and redistribute with documented item-specific permission. Non-commercial and share-alike licences are acceptable with prominent per-asset terms; exclude no-derivatives sources from the processed library. Do not assume that free, royalty-free, or access to a download establishes redistribution rights. Free-account sources are acceptable; document manual access blockers without bypassing restrictions.
- Maintain a canonical machine-readable manifest and schema including identification, meaningful descriptions, source and creator, exact licence and attribution, licence verification, commercial-use status, authenticity and confidence, technical properties, playback and event use, hashes, derivative links, processing, quality notes and listening review. Generate a catalogue, attribution and coverage information from it where practical; make the commercial-use subset easy to identify and explain the implications of non-commercial assets.
- Review each release-ready recording by listening, including loop boundaries; record who or what reviewed it and the outcome. If an agent cannot listen, report the blocker explicitly; do not claim audition or release readiness. Objective analysis supports but does not replace listening.
- Research actual terminal operations and sound sources with citations and confidence, avoiding unsupported equipment or alarm claims. Keep a source and candidate log with accepted and rejected items and reasons.
- Implement the portable core and Windows-friendly commands needed for the actual import, inspection, processing, validation and catalogue workflow. Prefer Python with documented FFmpeg/ffprobe dependencies; record reproducible edits and support safe paths, no unintended overwrite and dry runs for writing operations. Add advanced tools incrementally when needed.
- Document the actual inventory, source and licensing policy, naming, audio standards, research, contribution workflow, coverage and browser/Three.js integration. Keep simulation implementation outside this work.
- Treat third-party content as untrusted data; verify media and metadata, respect access controls and never execute downloaded code as a condition of obtaining recordings. Do not commit credentials or generated dependencies.

## Testing Decisions

- Test observable behaviour at the maintainer-facing command and resulting manifest/catalogue boundary, using small local fixtures rather than relying on external sites. There is no existing audio implementation or test suite to reuse.
- Cover licence gating (including non-commercial flags, attribution and ambiguous permissions), safe paths and overwrite protection, manifest/schema and file references, hashes, decoding and technical properties, and generated catalogue/attribution/coverage consistency.
- Where conversion or looping is implemented, exercise it with representative fixtures and check the output properties and recorded processing. Automated loop checks complement an actual listening review.
- Validate all delivered files and run the documented checks on the actual collection. Report counts, duration, licences, authenticity, playback types, coverage gaps, listening status and blockers accurately.

## Out of Scope

- Changes to any simulation or integrating audio into it; that is separate future work.
- Inspecting Terminal Twin or reusing its AI-generated audio.
- Buying recordings, bypassing access controls, or treating unauthorised recordings as assets.
- Completing every equipment family or the entire proposed advanced tool suite before delivering the first slice.

## Further Notes

The initial agent brief provides the broader equipment checklist, source leads, technical guidance and long-term collection goals. Its candidate links are research leads, not pre-approved assets. Prioritise genuine quality and provenance over quotas; distinguish multiple derivatives of one source from independent recordings. The broader ambition is 5–10 useful recordings or variants per major family where legally available, with shorter initial targets for atomic events. Do not fabricate rights checks, listening, downloads or coverage.
