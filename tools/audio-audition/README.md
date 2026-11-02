# Local audio audition tool

This static page lets a human listener play the 124 master recordings in the two collection manifests, switch to available MP3 previews, and save a compact review. Each review has a 1–5 star rating, selectable tags, playhead start/end markers, and an optional note. Save moves the item from **To review** to **Saved**; saved items can be reopened and updated. When present, the page also shows local YAMNet event suggestions and seek buttons for its highest-scoring times; these may be incorrect and are only triage hints.

From the repository root, start the range-enabled local server:

```sh
python tools/audio-audition/serve.py
```

Open <http://localhost:8000/tools/audio-audition/>. Search or filter recordings, listen with the browser player, fill in notes, save each review, then export a JSON file. The exported notes can be shared for follow-up and do not themselves change the canonical review status.

The page shows each track's full duration immediately and includes a seek bar, 10-second rewind/forward buttons, and browser-native audio controls. The server supports HTTP byte ranges so the browser can seek through large files without downloading all of them first.

The page reads the manifests and optional YAMNet report from the repository. Pressing Save writes or updates one review in `docs/listening-reviews.json` in this working copy. Each entry records the collection and asset ID, source path, rating, selected tags, start/end seconds, optional note and reviewer, and save time. The file can be committed and pushed later so the notes can be actioned. The page does not change asset manifests or release status. Audio and review notes stay on this machine; the server binds to localhost by default and uses no external services.
