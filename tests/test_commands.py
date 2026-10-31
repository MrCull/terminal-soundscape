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

if __name__ == '__main__':
    unittest.main()

