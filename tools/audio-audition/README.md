# Local audio audition tool

This static page lets a human listener play the 124 master recordings in the two collection manifests, switch to available MP3 previews, and save listening notes in the browser. It does not send audio or notes over the network, change manifests, or mark anything release-ready. Notes remain in browser local storage until exported.

From the repository root, start a local server:

```sh
python -m http.server 8000
```

Open <http://localhost:8000/tools/audio-audition/>. Search or filter recordings, listen with the browser player, fill in notes, save each review, then export a JSON file. The exported notes can be shared for follow-up and do not themselves change the canonical review status.

The page reads `manifest.json`, `first-collection/manifest.json`, and the first collection's preview manifest. It needs to be served from the repository root so the media paths resolve. It uses no external libraries or services.
