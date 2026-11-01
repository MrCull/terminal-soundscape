import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / 'soundscape.py'

def run(*args):
    return subprocess.run([sys.executable, str(CLI), *map(str, args)], capture_output=True, text=True)

def fixture(root):
    source = root / 'tone.wav'
    with wave.open(str(source), 'wb') as f:
        f.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
        f.writeframes(b'\x01\x00' * 4800)
    return source

def metadata_fixture():
    return {'id':'crane-1', 'description':'Bridge crane', 'source_url':'https://example.org/item', 'creator':'Recorder', 'license':'CC-BY-NC-4.0', 'license_url':'https://creativecommons.org/licenses/by-nc/4.0/', 'rights_evidence_url':'https://example.org/item', 'rights_verified_date':'2026-10-31', 'attribution':'Recorder, Bridge crane', 'authenticity':'substitute', 'authenticity_evidence':'source description', 'event':'crane movement', 'playback':'full-event', 'playback_guidance':'Play once', 'processing':'None', 'quality_notes':'fixture', 'review_status':'pending', 'reviewer':'none', 'review_notes':'Not listened'}

class Commands(unittest.TestCase):
    def test_validate_rejects_invalid_manifest_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'manifest.json').write_text(json.dumps({'version': 2, 'assets': []}))
            self.assertNotEqual(run('validate', '--root', root).returncode, 0)

    def test_catalogue_protects_existing_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'COVERAGE.md').write_text('keep me')
            result = run('catalogue', '--root', root)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((root / 'COVERAGE.md').read_text(), 'keep me')
            self.assertFalse((root / 'CATALOGUE.md').exists())

    def test_original_source_hash_and_validation_rejects_bad_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / 'original.bin'
            original.write_bytes(b'original recording')
            meta = root / 'metadata.json'
            meta.write_text(json.dumps(metadata_fixture()))
            result = run('import', fixture(root), meta, '--original-source', original, '--root', root)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest_path = root / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest['assets'][0]['source_sha256'], 'b9847a4fdf31702fb60bd2f225b53a79a922bd6c6f9a1a5f88f21c4a12134d2d')
            self.assertNotEqual(manifest['assets'][0]['source_sha256'], manifest['assets'][0]['sha256'])
            manifest['assets'][0]['source_sha256'] = 'invalid'
            manifest_path.write_text(json.dumps(manifest))
            self.assertNotEqual(run('validate', '--root', root).returncode, 0)

    def test_validate_rejects_silent_audio_even_when_metadata_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            meta = root / 'metadata.json'
            meta.write_text(json.dumps(metadata_fixture()))
            source = fixture(root)
            self.assertEqual(run('import', source, meta, '--original-source', source, '--root', root).returncode, 0)
            audio = root / 'audio' / 'crane-1.wav'
            with wave.open(str(audio), 'wb') as f:
                f.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
                f.writeframes(b'\x00\x00' * 4800)
            manifest_path = root / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            import hashlib
            manifest['assets'][0]['sha256'] = hashlib.sha256(audio.read_bytes()).hexdigest()
            manifest['assets'][0]['audio'] = json.loads(run('inspect', audio).stdout)
            manifest_path.write_text(json.dumps(manifest))
            self.assertNotEqual(run('validate', '--root', root).returncode, 0)

    def test_validation_rejects_invalid_audio_even_if_properties_match(self):
        import hashlib
        for channels, rate, sample in ((1, 44100, 1), (3, 48000, 1), (1, 48000, 32767)):
            with self.subTest(channels=channels, rate=rate, sample=sample), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                meta = root / 'metadata.json'
                meta.write_text(json.dumps(metadata_fixture()))
                source = fixture(root)
                self.assertEqual(run('import', source, meta, '--original-source', source, '--root', root).returncode, 0)
                audio = root / 'audio' / 'crane-1.wav'
                with wave.open(str(audio), 'wb') as f:
                    f.setparams((channels, 2, rate, 0, 'NONE', 'not compressed'))
                    f.writeframes(sample.to_bytes(2, 'little', signed=True) * channels * 100)
                manifest_path = root / 'manifest.json'
                manifest = json.loads(manifest_path.read_text())
                manifest['assets'][0]['sha256'] = hashlib.sha256(audio.read_bytes()).hexdigest()
                manifest['assets'][0]['audio'] = json.loads(run('inspect', audio).stdout)
                manifest_path.write_text(json.dumps(manifest))
                self.assertNotEqual(run('validate', '--root', root).returncode, 0)

    def test_reviewed_classification_closes_only_its_coverage_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            meta = root / 'metadata.json'
            meta.write_text(json.dumps({**metadata_fixture(), 'priority_category': 'crane movement', 'review_status': 'reviewed', 'reviewer': 'test listener', 'review_notes': 'listened'}))
            source = fixture(root)
            self.assertEqual(run('import', source, meta, '--original-source', source, '--root', root).returncode, 0)
            self.assertEqual(run('catalogue', '--root', root).returncode, 0)
            coverage = (root / 'COVERAGE.md').read_text(encoding='utf-8')
            self.assertIn('crane movement: crane-1', coverage)
            self.assertEqual(coverage.count('gap ? no reviewed recording classified'), 5)

    def test_inspect_reports_pcm_properties(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run('inspect', fixture(Path(tmp)))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['sample_rate'], 48000)
            self.assertEqual(json.loads(result.stdout)['duration_seconds'], 0.1)

    def test_import_rejects_unverified_rights(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata = root / 'metadata.json'
            metadata.write_text(json.dumps({'license': 'unknown'}))
            result = run('import', fixture(root), metadata, '--original-source', root / 'tone.wav', '--root', root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('rights', result.stderr)
            self.assertFalse((root / 'manifest.json').exists())

    def test_import_validate_and_catalogue_track_a_recording(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = fixture(root)
            metadata = root / 'metadata.json'
            metadata.write_text(json.dumps(metadata_fixture()))
            result = run('import', source, metadata, '--original-source', source, '--root', root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(run('validate', '--root', root).returncode, 0)
            report = run('catalogue', '--root', root)
            self.assertEqual(report.returncode, 0, report.stderr)
            self.assertIn('commercial use: False', report.stdout)
            self.assertIn('Recorder, Bridge crane', report.stdout)
            self.assertNotEqual(run('import', source, metadata, '--original-source', source, '--root', root).returncode, 0)
            (root / 'audio' / 'crane-1.wav').write_bytes(b'changed')
            self.assertNotEqual(run('validate', '--root', root).returncode, 0)

    def test_validation_rejects_paths_outside_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata = {'id':'x', 'description':'x', 'source_url':'https://example.org', 'creator':'x', 'license':'CC0-1.0', 'license_url':'https://creativecommons.org/publicdomain/zero/1.0/', 'rights_evidence_url':'https://example.org', 'rights_verified_date':'2026-10-31', 'attribution':'x', 'authenticity':'x', 'authenticity_evidence':'x', 'event':'x', 'playback':'one-shot', 'playback_guidance':'x', 'processing':'none', 'quality_notes':'x', 'review_status':'pending', 'reviewer':'none', 'review_notes':'pending', 'path':'../outside.wav'}
            (root / 'manifest.json').write_text(json.dumps({'version':1, 'assets':[metadata]}))
            result = run('validate', '--root', root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('unsafe path', result.stderr)

    def test_empty_catalogue_reports_gaps_and_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(run('catalogue', '--root', root, '--dry-run').returncode, 0)
            self.assertFalse((root / 'browser.json').exists())
            self.assertEqual(run('catalogue', '--root', root).returncode, 0)
            self.assertEqual(json.loads((root / 'browser.json').read_text())['assets'], [])
            coverage = (root / 'COVERAGE.md').read_text(encoding='utf-8')
            self.assertIn('Recordings: 0', coverage)
            self.assertEqual(coverage.count('gap ? no reviewed recording classified'), 6)

    def test_catalogue_generates_browser_mapping_and_reports_for_pending_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata = {**metadata_fixture(), 'license': 'CC-BY-NC-SA-4.0', 'license_url': 'https://creativecommons.org/licenses/by-nc-sa/4.0/'}
            meta = root / 'metadata.json'
            meta.write_text(json.dumps(metadata))
            self.assertEqual(run('import', fixture(root), meta, '--original-source', root / 'tone.wav', '--root', root).returncode, 0)
            result = run('catalogue', '--root', root)
            self.assertEqual(result.returncode, 0, result.stderr)
            mapping = json.loads((root / 'browser.json').read_text())
            self.assertEqual(mapping['assets'][0]['path'], 'audio/crane-1.wav')
            self.assertEqual(mapping['assets'][0]['event'], 'crane movement')
            self.assertEqual(mapping['assets'][0]['review_status'], 'pending')
            self.assertFalse(mapping['assets'][0]['commercial_use'])
            self.assertTrue(mapping['assets'][0]['share_alike'])
            attribution = (root / 'ATTRIBUTION.md').read_text(encoding='utf-8')
            coverage = (root / 'COVERAGE.md').read_text(encoding='utf-8')
            self.assertIn('Recorder, Bridge crane', attribution)
            self.assertIn('CC-BY-NC-SA-4.0', attribution)
            self.assertIn('pending', coverage)
            self.assertIn('substitute', coverage)
            self.assertIn('0.1', coverage)


if __name__ == '__main__':
    unittest.main()
