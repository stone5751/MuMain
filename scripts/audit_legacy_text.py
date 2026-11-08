"""Read-only inventory of v1.37.0 installed English skill/quest BMD texts."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from audit_zh_cn import write_tsv


def decode_record(data):
    key = bytes([0xFC, 0xCF, 0xAB])
    return bytes(value ^ key[i % 3] for i, value in enumerate(data))


def decode_text(data):
    raw = data.split(b'\0', 1)[0]
    try:
        return raw.decode('utf-8'), 'utf-8'
    except UnicodeDecodeError:
        return raw.decode('utf-8', errors='backslashreplace'), 'invalid UTF-8 bytes escaped; original unchanged'


def fixed_names(path, count, record_size, offset, length):
    data = path.read_bytes()
    assert len(data) in (count * record_size, count * record_size + 4), path
    result = []
    for index in range(count):
        record = decode_record(data[index * record_size:(index + 1) * record_size])
        name, encoding = decode_text(record[offset:offset + length])
        if name:
            result.append((index, name, encoding))
    return result


def quest_words(path):
    data, offset, result = path.read_bytes(), 0, []
    while offset < len(data):
        index, length = struct.unpack('<ih', decode_record(data[offset:offset + 6]))
        offset += 6
        assert 0 <= length <= 1024 and offset + length <= len(data), 'Invalid QuestWords record'
        text, encoding = decode_text(decode_record(data[offset:offset + length]))
        result.append((index, text, encoding))
        offset += length
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    files = {name: args.data / 'Local/Eng' / name for name in ['skill_eng.bmd', 'Quest_eng.bmd', 'QuestWords_eng.bmd']}
    before = {name: hashlib.sha256(p.read_bytes()).hexdigest() for name, p in files.items()}
    inventories = {
        'skills': fixed_names(files['skill_eng.bmd'], 650, 108, 0, 50),
        'quest-titles': fixed_names(files['Quest_eng.bmd'], 200, 744, 6, 32),
        'quest-words': quest_words(files['QuestWords_eng.bmd']),
    }
    for name, rows in inventories.items():
        write_tsv(args.output, name + '.tsv', ['id', 'english', 'encoding'], rows)
    assert before == {name: hashlib.sha256(p.read_bytes()).hexdigest() for name, p in files.items()}
    result = dict(counts={k: len(v) for k, v in inventories.items()}, sha256=before,
                  invalid_utf8_ids={k: [row[0] for row in v if row[2] != 'utf-8'] for k, v in inventories.items()},
                  note='Read-only text extraction; no BMD modifications and no gameplay availability inference.')
    (args.output / 'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
