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

class Commands(unittest.TestCase):
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
            result = run('import', fixture(root), metadata, '--root', root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('rights', result.stderr)
            self.assertFalse((root / 'manifest.json').exists())

    def test_import_validate_and_catalogue_track_a_recording(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = fixture(root)
            metadata = root / 'metadata.json'
            metadata.write_text(json.dumps({'id':'crane-1', 'description':'Bridge crane', 'source_url':'https://example.org/item', 'creator':'Recorder', 'license':'CC-BY-NC-4.0', 'license_url':'https://creativecommons.org/licenses/by-nc/4.0/', 'rights_evidence_url':'https://example.org/item', 'rights_verified_date':'2026-10-31', 'attribution':'Recorder, Bridge crane', 'authenticity':'substitute', 'authenticity_evidence':'source description', 'event':'crane movement', 'playback':'full-event', 'playback_guidance':'Play once', 'processing':'None', 'quality_notes':'fixture', 'review_status':'pending', 'reviewer':'none', 'review_notes':'Not listened'}))
            result = run('import', source, metadata, '--root', root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(run('validate', '--root', root).returncode, 0)
            report = run('catalogue', '--root', root)
            self.assertEqual(report.returncode, 0, report.stderr)
            self.assertIn('commercial use: False', report.stdout)
            self.assertIn('Recorder, Bridge crane', report.stdout)
            self.assertNotEqual(run('import', source, metadata, '--root', root).returncode, 0)
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
            self.assertIn('All six priority categories are gaps', coverage)

    def test_catalogue_generates_browser_mapping_and_reports_for_pending_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata = {'id':'crane-1', 'description':'Bridge crane', 'source_url':'https://example.org/item', 'creator':'Recorder', 'license':'CC-BY-NC-SA-4.0', 'license_url':'https://creativecommons.org/licenses/by-nc-sa/4.0/', 'rights_evidence_url':'https://example.org/item', 'rights_verified_date':'2026-10-31', 'attribution':'Recorder, Bridge crane', 'authenticity':'substitute', 'authenticity_evidence':'source description', 'event':'crane movement', 'playback':'full-event', 'playback_guidance':'Play once', 'processing':'None', 'quality_notes':'fixture', 'review_status':'pending', 'reviewer':'none', 'review_notes':'Not listened'}
            meta = root / 'metadata.json'
            meta.write_text(json.dumps(metadata))
            self.assertEqual(run('import', fixture(root), meta, '--root', root).returncode, 0)
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


