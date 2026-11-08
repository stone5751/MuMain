"""Apply reviewed ID + English-name mappings without reformatting JSON files."""
import argparse
import csv
import json
import re
from pathlib import Path

from audit_zh_cn import ROOT


def update_file(path, mappings, seen):
    text = path.read_text(encoding='utf-8')
    data = json.loads(text)
    is_item = 'items' in data
    rows = [r for r in data.get('items', data.get('monsters', [])) if 'name' in r]
    # These files currently contain only row-level names. Refuse a new layout.
    blocks = list(re.finditer(r'"name": \{[^{}]*\}', text))
    if len(blocks) != len(rows):
        raise ValueError(f'Unexpected name layout: {path}')
    changes = []
    for row, block in zip(rows, blocks):
        names = json.loads('{' + block.group() + '}')['name']
        if names != row['name']:
            raise ValueError(f'Name block does not match parsed row: {path}')
        ids = f"{data['group']},{row['number']}" if is_item else ','.join(str(n['number']) for n in row['numbers'])
        key = ('item' if is_item else row['kind'], ids)
        if key not in mappings:
            continue
        entry = mappings[key]
        if names.get('en') != entry['english']:
            raise ValueError(f'English identity mismatch: {key}')
        if 'zh-CN' in names and names['zh-CN'] != entry['zh-CN']:
            raise ValueError(f'Refusing existing translation change: {key}')
        seen.add(key)
        if 'zh-CN' in names:
            continue
        old = block.group()
        value = json.dumps(entry['zh-CN'], ensure_ascii=False)
        if '\n' in old:
            insertion = old.rfind('\n')
            indent = re.search(r'\n( +)"', old).group(1)
            new = old[:insertion].rstrip() + ',\n' + indent + '"zh-CN": ' + value + old[insertion:]
        else:
            new = old[:-1].rstrip() + ', "zh-CN": ' + value + '}'
        changes.append((block.start(), block.end(), new))
    for start, end, replacement in reversed(changes):
        text = text[:start] + replacement + text[end:]
    return text, len(changes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mapping', type=Path)
    args = parser.parse_args()
    entries = list(csv.DictReader(args.mapping.open(encoding='utf-8-sig'), delimiter='\t'))
    mappings = {(e['kind'], e['ids']): e for e in entries}
    if len(mappings) != len(entries) or any(not e['zh-CN'] or not e['source'] for e in entries):
        raise ValueError('Duplicate IDs, empty translations or missing review sources')
    paths = sorted((ROOT / 'src/bin/Data/Items').glob('Group*.json'))
    paths.append(ROOT / 'src/bin/Data/Monsters/Monsters.json')
    seen, updates = set(), []
    for path in paths:
        text, count = update_file(path, mappings, seen)
        if count:
            updates.append((path, text, count))
    if seen != mappings.keys():
        raise ValueError(f'Unknown IDs: {mappings.keys() - seen}')
    for path, text, count in updates:
        path.write_text(text, encoding='utf-8', newline='\n')
        print(f'{path.name}: {count} names added')


if __name__ == '__main__':
    main()
