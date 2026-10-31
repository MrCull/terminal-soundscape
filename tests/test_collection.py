import hashlib
import json
import shutil
import tempfile
import unittest
import wave
from pathlib import Path

from soundscape.catalogue import CollectionError, coverage_data, import_media, inspect_media, prepare_browser_candidates, render_attribution, render_browser_mapping, render_catalogue, validate


class CollectionCommandsTest(unittest.TestCase):
    def test_empty_collection_validates_and_generates_catalogue(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.json"
            manifest.write_text('{"schema_version":1,"assets":[]}', encoding="utf-8")
            self.assertEqual(validate(manifest), [])
            self.assertIn("# Audio catalogue", render_catalogue(manifest))

    def test_malformed_manifest_and_asset_shapes_fail_without_crashing(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.json"
            manifest.write_text('[]', encoding="utf-8")
            with self.assertRaisesRegex(CollectionError, "Expected schema_version"):
                validate(manifest)
            manifest.write_text('{"schema_version":1,"assets":[null]}', encoding="utf-8")
            self.assertTrue(any("expected an object" in error for error in validate(manifest)))

    def test_valid_wav_requires_matching_hash_and_technical_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "asset.wav"
            with wave.open(str(audio), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(48000)
                wav.writeframes(b"\x01\0" * 480)
            asset = {
                "id": "crane-01", "title": "Crane", "category": "crane", "file": "asset.wav",
                "source_url": "https://example.test", "creator": "Example", "license": "CC0",
                "source_downloaded_on": "2026-10-31", "codec": "PCM", "bit_depth": 16, "file_size_bytes": audio.stat().st_size,
                "source_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(), "authenticity_confidence": "verified fixture", "quality_notes": "fixture", "event_guidance": "test", "processing": [],
                "attribution": "Example", "commercial_use": "allowed", "authenticity": "authentic",
                "license_url": "https://creativecommons.org/publicdomain/zero/1.0/", "license_verified_on": "2026-10-31", "share_alike": False,
                "playback": "one_shot", "processing": [], "derivatives": [], "quality_notes": "fixture", "authenticity_confidence": "verified fixture", "event_guidance": "test", "source_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(), "review": {"status": "not_reviewed"},
                "sha256": hashlib.sha256(audio.read_bytes()).hexdigest(), "sample_rate_hz": 48000,
                "channels": 1, "duration_seconds": 0.01
            }
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"schema_version": 1, "assets": [asset]}), encoding="utf-8")
            self.assertEqual(validate(manifest), [])
            derivative = root / "preview.mp3"
            derivative.write_bytes(b"candidate")
            asset["derivatives"] = [{"file":"preview.mp3", "sha256":"0" * 64}]
            manifest.write_text(json.dumps({"schema_version": 1, "assets": [asset]}), encoding="utf-8")
            self.assertTrue(any("derivatives[0]: sha256 mismatch" in error for error in validate(manifest)))

    def test_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = {"id":"escape", "title":"x", "category":"x", "file":"../outside.wav", "source_url":"x", "creator":"x", "license":"x", "attribution":"x", "commercial_use":"allowed", "authenticity":"x", "playback":"x", "review":{"status":"not_reviewed"}}
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"schema_version": 1, "assets": [asset]}), encoding="utf-8")
            self.assertTrue(any("escapes collection" in error for error in validate(manifest)))

    def test_release_ready_requires_rights_verification_and_real_listener(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "asset.wav"
            with wave.open(str(audio), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(48000)
                wav.writeframes(b"\0\0" * 480)
            asset = {
                "id": "crane-01", "title": "Crane", "category": "crane", "file": "asset.wav",
                "source_url": "https://example.test", "creator": "Example", "license": "unknown",
                "source_downloaded_on": "2026-10-31", "codec": "PCM", "bit_depth": 16, "file_size_bytes": audio.stat().st_size,
                "source_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(), "authenticity_confidence": "unknown", "quality_notes": "not reviewed", "event_guidance": "test", "processing": [],
                "license_url": "unknown", "license_verified_on": None, "attribution": "Example",
                "commercial_use": "unknown", "share_alike": False, "authenticity": "authentic", "playback": "one_shot",
                "sha256": hashlib.sha256(audio.read_bytes()).hexdigest(), "derivatives": [], "review": {"status": "release_ready", "listener": None}
            }
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"schema_version": 1, "assets": [asset]}), encoding="utf-8")
            errors = validate(manifest)
            self.assertTrue(any("named listener" in error for error in errors))
            self.assertTrue(any("loop-boundary review" in error for error in errors))
            self.assertTrue(any("verified item-level rights" in error for error in errors))

    def test_catalogue_makes_share_alike_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.json"
            manifest.write_text(json.dumps({"schema_version": 1, "assets": [{"id":"a", "title":"Port", "file":"x.ogg", "category":"ambience", "license":"CC BY-SA 3.0", "commercial_use":"allowed", "share_alike":True, "authenticity":"authentic", "review":{"status":"candidate_not_auditioned"}}]}), encoding="utf-8")
            report = render_catalogue(manifest)
            self.assertIn("Share-alike", report)
            self.assertIn("True", report)

    def test_generated_delivery_reports_keep_candidates_out_of_release_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.json"
            asset = {"id":"port-1", "title":"Port", "file":"port.ogg", "category":"harbour_ambience", "license":"CC BY-SA 3.0", "license_url":"https://creativecommons.org/licenses/by-sa/3.0/", "attribution":"Creator, Port, CC BY-SA 3.0", "commercial_use":"allowed", "share_alike":True, "authenticity":"authentic", "review":{"status":"candidate_not_auditioned"}, "duration_seconds":12.0}
            manifest.write_text(json.dumps({"schema_version":1,"assets":[asset]}), encoding="utf-8")
            coverage = coverage_data(manifest)
            self.assertEqual(coverage["audio_candidate_count"], 1)
            self.assertEqual(coverage["release_ready_count"], 0)
            self.assertEqual(coverage["browser_ready_count"], 0)
            self.assertEqual(coverage["categories"]["harbour_ambience"]["candidate_count"], 1)
            self.assertIn("CC BY-SA 3.0", render_attribution(manifest))
            mapping = json.loads(render_browser_mapping(manifest))
            self.assertIsNone(mapping["assets"][0]["event_mapping"])
            self.assertFalse(mapping["assets"][0]["browser_ready"])

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is required for browser conversion")
    def test_browser_conversion_records_hashes_and_remains_unreviewed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "source.wav"
            with wave.open(str(audio), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(48000)
                wav.writeframes(b"\x01\0" * 480)
            digest = hashlib.sha256(audio.read_bytes()).hexdigest()
            asset = {"id":"fixture", "file":"source.wav", "sha256":digest, "license":"CC0", "license_url":"https://creativecommons.org/publicdomain/zero/1.0/", "attribution":"Fixture", "commercial_use":"allowed", "share_alike":False}
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"schema_version":1,"assets":[asset]}), encoding="utf-8")
            prepare_browser_candidates(manifest, "browser", dry_run=True)
            self.assertFalse((root / "browser").exists())
            output = prepare_browser_candidates(manifest, "browser")
            preview_manifest = json.loads((output / "preview-manifest.json").read_text(encoding="utf-8"))
            preview = preview_manifest["assets"][0]
            self.assertTrue(preview["browser_compatible_preview"])
            self.assertFalse(preview["release_ready"])
            self.assertEqual(preview["source_sha256"], digest)
            self.assertNotEqual(preview["sha256"], digest)
            with self.assertRaisesRegex(CollectionError, "Refusing to overwrite"):
                prepare_browser_candidates(manifest, "browser")

    def test_import_dry_run_does_not_write_and_import_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text('{"schema_version":1,"assets":[]}', encoding="utf-8")
            source = root / "source.ogg"
            source.write_bytes(b"fixture")
            target = import_media(source, manifest, "assets/candidates/source.ogg", dry_run=True)
            self.assertFalse(target.exists())
            target = import_media(source, manifest, "assets/candidates/source.ogg")
            self.assertEqual(target.read_bytes(), b"fixture")
            with self.assertRaisesRegex(CollectionError, "Refusing to overwrite"):
                import_media(source, manifest, "assets/candidates/source.ogg")

    def test_import_rejects_destination_outside_collection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text('{"schema_version":1,"assets":[]}', encoding="utf-8")
            source = root / "source.ogg"
            source.write_bytes(b"fixture")
            with self.assertRaisesRegex(CollectionError, "escapes collection"):
                import_media(source, manifest, "../outside.ogg", dry_run=True)

    def test_inspection_reports_hash_and_wav_properties(self):
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / "sample.wav"
            with wave.open(str(audio), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(48000)
                wav.writeframes(b"\0\0" * 480)
            result = inspect_media(audio)
            self.assertEqual(result["bytes"], audio.stat().st_size)
            if "ffprobe" in result:
                self.assertEqual(result["ffprobe"]["streams"][0]["sample_rate"], "48000")
            else:
                self.assertEqual(result["audio"]["sample_rate_hz"], 48000)


if __name__ == "__main__":
    unittest.main()
