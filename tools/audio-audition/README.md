# Local audio audition tool

This static page lets a human listener play the 124 master recordings in the two collection manifests, switch to available MP3 previews, and save listening notes in the browser. When present, it also shows local YAMNet sound-event suggestions and seek buttons for its highest-scoring time windows. These may be incorrect and are only triage hints. It does not send audio or notes over the network, change manifests, or mark anything release-ready. Notes remain in browser local storage until exported.

From the repository root, start the range-enabled local server:

```sh
python tools/audio-audition/serve.py
```

Open <http://localhost:8000/tools/audio-audition/>. Search or filter recordings, listen with the browser player, fill in notes, save each review, then export a JSON file. The exported notes can be shared for follow-up and do not themselves change the canonical review status.

The page shows each track's full duration immediately and includes a seek bar, 10-second rewind/forward buttons, and browser-native audio controls. The server supports HTTP byte ranges so the browser can seek through large files without downloading all of them first.

The page reads `manifest.json`, `first-collection/manifest.json`, the first collection's preview manifest, and the optional YAMNet report at `docs/generated/audio-event-tags.json`. The server runs from the repository root so media paths resolve. The page and server use no external libraries or services.
