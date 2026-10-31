import argparse
import hashlib
import json
import sys
import wave
from pathlib import Path

LICENSES = {'CC0-1.0': (True, False), 'CC-BY-4.0': (True, False),
            'CC-BY-SA-4.0': (True, True), 'CC-BY-NC-4.0': (False, False),
            'CC-BY-NC-SA-4.0': (False, True)}
REQUIRED = ('id', 'description', 'source_url', 'creator', 'license', 'license_url',
            'rights_evidence_url', 'rights_verified_date', 'attribution', 'authenticity',
            'authenticity_evidence', 'event', 'playback', 'playback_guidance',
            'processing', 'quality_notes', 'review_status', 'reviewer', 'review_notes')


def inspect(path):
    with wave.open(str(path), 'rb') as audio:
        channels, width, rate, frames = (audio.getnchannels(), audio.getsampwidth(),
                                         audio.getframerate(), audio.getnframes())
        if audio.getcomptype() != 'NONE' or width != 2:
            raise ValueError('only 16-bit PCM WAV is supported')
        data = audio.readframes(frames)
        if len(data) != frames * channels * width:
            raise ValueError('truncated audio')
        samples = [int.from_bytes(data[i:i+2], 'little', signed=True) for i in range(0, len(data), 2)]
        peak = max((abs(x) for x in samples), default=0)
        return {'sample_rate': rate, 'channels': channels, 'bit_depth': width * 8,
                'duration_seconds': frames / rate, 'peak': peak, 'clipped_samples': sum(abs(x) >= 32767 for x in samples)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(root):
    path = root / 'manifest.json'
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {'version': 1, 'assets': []}


def safe(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or path == root.resolve():
        raise ValueError('unsafe path')
    return path


def check_metadata(m):
    if any(not m.get(k) for k in REQUIRED) or m.get('license') not in LICENSES:
        raise ValueError('rights or required metadata incomplete; permitted licences are ' + ', '.join(LICENSES))
    if m['playback'] not in ('one-shot', 'full-event', 'loop'):
        raise ValueError('invalid playback')
    if m['review_status'] not in ('pending', 'reviewed'):
        raise ValueError('invalid review status')
    if m['review_status'] == 'reviewed' and (not m['reviewer'] or not m['review_notes']):
        raise ValueError('review requires reviewer and notes')


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('inspect'); p.add_argument('path')
    p = sub.add_parser('import'); p.add_argument('source'); p.add_argument('metadata'); p.add_argument('--root', default='.'); p.add_argument('--dry-run', action='store_true')
    for cmd in ('validate', 'catalogue'):
        p = sub.add_parser(cmd); p.add_argument('--root', default='.'); p.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.command == 'inspect':
        print(json.dumps(inspect(args.path), indent=2)); return
    root = Path(args.root).resolve()
    manifest = load(root)
    if args.command == 'import':
        m = json.loads(Path(args.metadata).read_text(encoding='utf-8-sig'))
        check_metadata(m)
        if not m['id'].replace('-', '').replace('_', '').isalnum() or not m['id'].isascii():
            raise ValueError('invalid id')
        if any(a['id'] == m['id'] for a in manifest['assets']): raise ValueError('duplicate id')
        source = Path(args.source)
        audio = inspect(source)
        if audio['sample_rate'] != 48000 or audio['channels'] not in (1, 2) or audio['peak'] == 0 or audio['clipped_samples']:
            raise ValueError('audio must be non-silent, unclipped 48 kHz mono or stereo 16-bit PCM WAV')
        dest = safe(root, 'audio/' + m['id'] + '.wav')
        if dest.exists(): raise ValueError('destination already exists')
        m.update({'path': dest.relative_to(root).as_posix(), 'source_sha256': sha(source), 'sha256': sha(source), 'audio': audio,
                  'commercial_use': LICENSES[m['license']][0], 'share_alike': LICENSES[m['license']][1]})
        manifest['assets'].append(m)
        if not args.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as out: out.write(source.read_bytes())
            (root / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(json.dumps(m, indent=2)); return
    for m in manifest['assets']:
        check_metadata(m)
        path = safe(root, m['path'])
        if sha(path) != m['sha256'] or inspect(path) != m['audio']: raise ValueError('hash or audio properties mismatch: ' + m['id'])
        if (m['commercial_use'], m['share_alike']) != LICENSES[m['license']]: raise ValueError('licence flags mismatch')
    if args.command == 'validate':
        print('Validated ' + str(len(manifest['assets'])) + ' assets'); return
    lines = ['# Sound catalogue', '', 'Commercial use depends on each asset licence; do not assume the entire collection is commercially usable.', '']
    for m in manifest['assets']:
        lines.extend([f"## {m['id']}", '', m['description'], '', f"- File: {m['path']}", f"- Licence: {m['license']} ({m['license_url']}); commercial use: {m['commercial_use']}; share alike: {m['share_alike']}", f"- Attribution: {m['attribution']}", f"- Source: {m['source_url']}", f"- Authenticity: {m['authenticity']}", f"- Playback: {m['playback']} — {m['playback_guidance']}", f"- Review: {m['review_status']} — {m['review_notes']}", ''])
    if not manifest['assets']: lines += ['No recordings are currently in the collection.', '']
    output = '\n'.join(lines)
    if not args.dry_run: (root / 'CATALOGUE.md').write_text(output, encoding='utf-8')
    print(output)

if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, KeyError, wave.Error, json.JSONDecodeError) as exc:
        print('Error: ' + str(exc), file=sys.stderr); sys.exit(1)

