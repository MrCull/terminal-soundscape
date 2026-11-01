import argparse
import hashlib
import json
import re
import sys
import wave
from collections import Counter
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
    if any(not isinstance(m.get(k), str) or not m[k].strip() for k in REQUIRED) or m.get('license') not in LICENSES:
        raise ValueError('rights or required metadata incomplete; permitted licences are ' + ', '.join(LICENSES))
    if m['playback'] not in ('one-shot', 'full-event', 'loop'):
        raise ValueError('invalid playback')
    if m['review_status'] not in ('pending', 'reviewed'):
        raise ValueError('invalid review status')
    if m['review_status'] == 'reviewed' and (not m['reviewer'] or not m['review_notes']):
        raise ValueError('review requires reviewer and notes')


def validate_manifest(manifest, root):
    if not isinstance(manifest, dict) or type(manifest.get('version')) is not int or manifest['version'] != 1 or not isinstance(manifest.get('assets'), list):
        raise ValueError('invalid manifest schema or version')
    seen = set()
    for m in manifest['assets']:
        if not isinstance(m, dict):
            raise ValueError('invalid asset')
        check_metadata(m)
        if any(not isinstance(m[k], str) or not m[k].strip() for k in REQUIRED):
            raise ValueError('invalid metadata types')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', m['id']) or m['id'] in seen:
            raise ValueError('invalid or duplicate id')
        seen.add(m['id'])
        if not isinstance(m.get('path'), str) or not m['path']:
            raise ValueError('invalid path')
        path = safe(root, m['path'])
        for key in ('source_sha256', 'sha256'):
            if not isinstance(m.get(key), str) or not re.fullmatch(r'[0-9a-f]{64}', m[key]):
                raise ValueError('invalid SHA-256: ' + key)
        if type(m.get('commercial_use')) is not bool or type(m.get('share_alike')) is not bool:
            raise ValueError('invalid licence flags')
        if not isinstance(m.get('audio'), dict):
            raise ValueError('invalid audio properties')
        properties = m['audio']
        if any(type(properties.get(k)) is not int for k in ('sample_rate', 'channels', 'bit_depth', 'peak', 'clipped_samples')) or type(properties.get('duration_seconds')) not in (int, float):
            raise ValueError('invalid audio properties')
        audio = inspect(path)
        check_audio(audio)
        if sha(path) != m['sha256'] or audio != m['audio']:
            raise ValueError('hash or audio properties mismatch: ' + m['id'])
        if (m['commercial_use'], m['share_alike']) != LICENSES[m['license']]:
            raise ValueError('licence flags mismatch')
        if 'priority_category' in m and m['priority_category'] not in PRIORITIES:
            raise ValueError('invalid priority category')


PRIORITIES = ('crane movement', 'container contact', 'carrier or tractor movement',
              'terminal warnings', 'reefer ambience', 'harbour ambience')


def check_audio(audio):
    if audio['sample_rate'] != 48000 or audio['channels'] not in (1, 2) or audio['peak'] == 0 or audio['clipped_samples']:
        raise ValueError('audio must be non-silent, unclipped 48 kHz mono or stereo 16-bit PCM WAV')


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('inspect'); p.add_argument('path')
    p = sub.add_parser('import'); p.add_argument('source'); p.add_argument('metadata'); p.add_argument('--root', default='first-collection'); p.add_argument('--dry-run', action='store_true'); p.add_argument('--original-source', required=True)
    for cmd in ('validate', 'catalogue'):
        p = sub.add_parser(cmd); p.add_argument('--root', default='first-collection'); p.add_argument('--dry-run', action='store_true')
    sub.choices['catalogue'].add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    if args.command == 'inspect':
        print(json.dumps(inspect(args.path), indent=2)); return
    root = Path(args.root).resolve()
    manifest = load(root)
    if args.command == 'import':
        validate_manifest(manifest, root)
        m = json.loads(Path(args.metadata).read_text(encoding='utf-8-sig'))
        check_metadata(m)
        if not m['id'].replace('-', '').replace('_', '').isalnum() or not m['id'].isascii():
            raise ValueError('invalid id')
        if any(a['id'] == m['id'] for a in manifest['assets']): raise ValueError('duplicate id')
        if 'priority_category' in m and m['priority_category'] not in PRIORITIES:
            raise ValueError('invalid priority category')
        source = Path(args.source)
        audio = inspect(source)
        check_audio(audio)
        dest = safe(root, 'audio/' + m['id'] + '.wav')
        if dest.exists(): raise ValueError('destination already exists')
        m.update({'path': dest.relative_to(root).as_posix(), 'source_sha256': sha(Path(args.original_source)), 'sha256': sha(source), 'audio': audio,
                  'commercial_use': LICENSES[m['license']][0], 'share_alike': LICENSES[m['license']][1]})
        manifest['assets'].append(m)
        if not args.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as out: out.write(source.read_bytes())
            (root / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(json.dumps(m, indent=2)); return
    validate_manifest(manifest, root)
    if args.command == 'validate':
        print('Validated ' + str(len(manifest['assets'])) + ' assets'); return
    generate_catalogue(manifest, root, args.dry_run, args.overwrite)


def generate_catalogue(manifest, root, dry_run, overwrite):
    lines = ['# Sound catalogue', '', 'Commercial use depends on each asset licence; do not assume the entire collection is commercially usable.', '']
    for m in manifest['assets']:
        lines.extend([f"## {m['id']}", '', m['description'], '', f"- File: {m['path']}", f"- Licence: {m['license']} ({m['license_url']}); commercial use: {m['commercial_use']}; share alike: {m['share_alike']}", f"- Attribution: {m['attribution']}", f"- Source: {m['source_url']}", f"- Authenticity: {m['authenticity']}", f"- Playback: {m['playback']} — {m['playback_guidance']}", f"- Review: {m['review_status']} — {m['review_notes']}", ''])
    if not manifest['assets']: lines += ['No recordings are currently in the collection.', '']
    output = '\n'.join(lines)
    assets = manifest['assets']
    mapping = {'version': 1, 'assets': [
        {k: m[k] for k in ('id', 'path', 'event', 'playback', 'playback_guidance',
                            'audio', 'license', 'license_url', 'attribution',
                            'commercial_use', 'share_alike', 'authenticity', 'review_status')}
        for m in assets]}
    attribution = ['# Attribution', '', 'Check each licence before distribution. Non-commercial and share-alike restrictions apply where marked.', '']
    for m in assets:
        attribution.extend([f"## {m['id']}", '', m['attribution'], '',
                            f"- Source: {m['source_url']}",
                            f"- Licence: {m['license']} ({m['license_url']}); commercial use: {m['commercial_use']}; share alike: {m['share_alike']}", ''])
    if not assets: attribution += ['No recordings are currently in the collection.', '']
    coverage = ['# Collection coverage', '', f"Recordings: {len(assets)}",
                f"Total duration: {sum(m['audio']['duration_seconds'] for m in assets):g} seconds", '']
    for label, key in (('Licences', 'license'), ('Playback types', 'playback'),
                       ('Authenticity', 'authenticity'), ('Listening status', 'review_status'),
                       ('Events', 'event')):
        counts = Counter(m[key] for m in assets)
        coverage.append(f"- {label}: " + (', '.join(f'{k}: {v}' for k, v in sorted(counts.items())) or 'none'))
    coverage += ['', 'Priority categories (reviewed and classified recordings only):']
    for category in PRIORITIES:
        reviewed = [m['id'] for m in assets if m.get('priority_category') == category and m['review_status'] == 'reviewed']
        coverage.append(f"- {category}: " + (', '.join(reviewed) if reviewed else 'gap ? no reviewed recording classified'))
    coverage += ['', 'Classification is a contributor assertion; check suitability and reviews before use.', '']
    if not dry_run:
        reports = (('CATALOGUE.md', output), ('ATTRIBUTION.md', '\n'.join(attribution)),
                              ('COVERAGE.md', '\n'.join(coverage)),
                              ('browser.json', json.dumps(mapping, indent=2, ensure_ascii=False) + '\n'))
        destinations = [(safe(root, name), content) for name, content in reports]
        if not overwrite and any(path.exists() for path, _ in destinations):
            raise ValueError('report already exists; use --overwrite to replace reports')
        for path, content in destinations:
            with path.open('w' if overwrite else 'x', encoding='utf-8', newline='\n') as output_file:
                output_file.write(content)
    print(output)

if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, KeyError, wave.Error, json.JSONDecodeError) as exc:
        print('Error: ' + str(exc), file=sys.stderr); sys.exit(1)
