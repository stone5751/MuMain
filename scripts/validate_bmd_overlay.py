"""Validate guarded display overlays against unchanged local BMD files."""
import argparse
import hashlib
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path
from audit_legacy_text import decode_record, decode_text, fixed_names
from validate_zh_cn import PRINTF

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / 'src/bin/Data/Local/BmdText.zh-CN.json'
LIMITS = {'skills': (650, 49), 'quest-titles': (200, 31),
          'quest-words': (1000000, 50), 'slides': (160, 255),
          'quest-dialogue': (1000000, 200), 'quest-summary': (1000000, 200)}
LEGACY_ENCODING = 'cp949-decoded-as-utf8-by-original-windows-loader'


def dialogue_ids(data):
    """Read actual NPC-body references; never infer a role from ID ordering."""
    result = set()
    for name, size, layout in [('QuestProgress.bmd', 41, '<IB9i'),
                               ('NPCDialogue.bmd', 88, '<I21i')]:
        blob = (data / 'Local' / name).read_bytes()
        assert len(blob) % size == 0, name
        for offset in range(0, len(blob), size):
            row = struct.unpack(layout, decode_record(blob[offset:offset + size]))
            result.add(row[2] if name == 'QuestProgress.bmd' else row[1])
    return result


def summary_ids(data):
    blob = (data / 'Local/QuestProgress.bmd').read_bytes()
    assert len(blob) % 41 == 0
    return {struct.unpack('<IB9i', decode_record(blob[i:i + 41]))[10]
            for i in range(0, len(blob), 41)}


def runtime_quest_words(path):
    """Mirror the existing Windows loader, including its malformed-UTF8 handling."""
    blob, offset, result, hashes = path.read_bytes(), 0, [], {}
    while offset < len(blob):
        number, size = struct.unpack('<ih', decode_record(blob[offset:offset + 6]))
        offset += 6
        assert 0 < size <= 1024 and offset + size <= len(blob)
        raw = decode_record(blob[offset:offset + size]).split(b'\0', 1)[0]
        offset += size
        try:
            text, encoding = raw.decode('utf-8'), 'utf-8'
        except UnicodeDecodeError:
            assert sys.platform == 'win32', 'Malformed source verification requires the original Windows decoder'
            import ctypes
            raw.decode('cp949')  # Verify the identified source encoding as well.
            buffer = ctypes.create_unicode_buffer(len(raw) + 1)
            assert ctypes.windll.kernel32.MultiByteToWideChar(65001, 0, raw, len(raw), buffer, len(buffer)) > 0
            text, encoding = buffer.value, LEGACY_ENCODING
            hashes[number] = hashlib.sha256(raw).hexdigest()
        result.append((number, text, encoding))
    return result, hashes


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON member: {key}')
        result[key] = value
    return result


def read_sources(data, hashes):
    directory = data / 'Local/Eng'
    actual = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in hashes}
    assert actual == hashes, 'BMD identity differs from the reviewed source files'
    words, legacy_hashes = runtime_quest_words(directory / 'QuestWords_eng.bmd')
    sources = {'skills': fixed_names(directory / 'skill_eng.bmd', 650, 108, 0, 50),
               'quest-titles': fixed_names(directory / 'Quest_eng.bmd', 200, 744, 6, 32),
               'quest-words': words, 'slides': []}
    decoded = decode_record((directory / 'slide_eng.bmd').read_bytes())
    assert len(decoded) == 8 + 5 * 8200
    for block in range(5):
        offset = 8 + block * 8200
        _, count = struct.unpack_from('<ii', decoded, offset)
        assert 0 <= count <= 32
        for slot in range(count):
            start = offset + 8 + slot * 256
            text, encoding = decode_text(decoded[start:start + 256])
            sources['slides'].append((block * 32 + slot, text, encoding))
    return {(kind, number): (text, encoding) for kind, rows in sources.items()
            for number, text, encoding in rows}, actual, legacy_hashes


def validate(data=None):
    doc = json.loads(OVERLAY.read_text(encoding='utf-8'), object_pairs_hook=unique)
    assert doc['formatVersion'] == 1 and doc['locale'] == 'zh-CN'
    sources, hashes, legacy_hashes = read_sources(data, doc['sourceSha256']) if data else ({}, {}, {})
    keys, counts = set(), Counter()
    body_ids = dialogue_ids(data) if data else set()
    summaries = summary_ids(data) if data else set()
    for row in doc['entries']:
        kind, number = row['kind'], row['id']
        assert kind in LIMITS and type(number) is int and 0 <= number < LIMITS[kind][0]
        key = ('quest-words' if kind in ('quest-dialogue', 'quest-summary') else kind), number
        assert key not in keys, f'Duplicate ID: {key}'
        keys.add(key)
        en, zh = row['english'], row['zh-CN']
        assert en and zh and '\0' not in en + zh and '\ufffd' not in zh
        encoding = row.get('sourceEncoding', 'utf-8')
        if encoding != 'utf-8':
            assert encoding == LEGACY_ENCODING and key[0] == 'quest-words'
            assert re.fullmatch('[0-9a-f]{64}', row['sourceBytesSha256'])
        else:
            assert '\ufffd' not in en and 'sourceBytesSha256' not in row
        assert len(zh.encode('utf-16-le')) // 2 <= LIMITS[kind][1], key
        assert PRINTF.findall(en) == PRINTF.findall(zh) and en.count('%') == zh.count('%'), key
        for pattern in [r'[;\r\n\t]', r'\{[^{}]*\}', r'(?<!\w)/[A-Za-z]+']:
            assert re.findall(pattern, en) == re.findall(pattern, zh), (key, pattern)
        if key[0] == 'quest-words':
            assert re.findall(r'\d+', en) == re.findall(r'\d+', zh), (key, 'numeric text changed')
        assert all(ord(c) >= 32 or c in '\r\n\t' for c in zh)
        if data:
            assert sources[key] == (en, encoding), f'ID/original mismatch: {key}'
            if encoding != 'utf-8':
                assert legacy_hashes[number] == row['sourceBytesSha256'], key
            if kind == 'quest-dialogue':
                assert number in body_ids, f'Not an NPC-body reference: {number}'
            if kind == 'quest-summary':
                assert number in summaries, f'Not a summary reference: {number}'
        counts[kind] += 1
    assert counts['skills'] == 66 and counts['slides'] == 20
    assert counts['quest-titles'] >= 2 and counts['quest-words'] >= 19 and counts['quest-dialogue'] >= 1
    assert sum(counts[k] for k in ('quest-words', 'quest-dialogue', 'quest-summary')) == 2288
    assert counts['quest-titles'] == 7
    assert OVERLAY.stat().st_size < 2 * 1024 * 1024 and len(keys) <= 4096
    if data:
        assert hashes == {name: hashlib.sha256((data / 'Local/Eng' / name).read_bytes()).hexdigest() for name in hashes}
    return {'entries': len(keys), 'counts': dict(counts), 'structure_tokens_lengths': 'passed',
            'real_bmd_id_and_hash_verification': 'passed; input files unchanged' if data else 'not run (no game assets in CI)',
            'source_sha256': hashes, 'in_game': 'NOT TESTED'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = json.dumps(validate(args.data), ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding='utf-8')
    print(report)
