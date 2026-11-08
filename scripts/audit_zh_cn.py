"""Inventory zh-CN coverage without changing source resources (Python stdlib only)."""
import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def resources(path):
    if not path.exists():
        return {}
    return {e.attrib['name']: e.findtext('value', '') for e in ET.parse(path).findall('data')}


def identifier(key):
    words = re.findall(r'[A-Za-z0-9]+', key)
    result = ''.join(w[0].upper() + w[1:] for w in words)
    return '_' + result if result[:1].isdigit() else result


def write_tsv(directory, name, columns, rows):
    with (directory / name).open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t')
        writer.writerow(columns)
        writer.writerows(rows)


def audit_resources(directory):
    summary, missing = {}, []
    for path in sorted((ROOT / 'src/Localization').glob('*.en.resx')):
        group = path.name.split('.')[0]
        en = resources(path)
        zh = resources(path.with_name(group + '.zh-CN.resx'))
        absent = [k for k in en if not zh.get(k)]
        summary[group] = dict(english=len(en), translated=len(en.keys() & zh.keys()),
                              missing=len(absent), same_as_english=sum(zh.get(k) == v for k, v in en.items()))
        missing.extend((group, k, identifier(k), en[k]) for k in absent)
    write_tsv(directory, 'missing-resources.tsv', ['group', 'key', 'identifier', 'english'], missing)
    return summary


def audit_names(directory):
    rows, counts = [], {}
    for path in sorted((ROOT / 'src/bin/Data/Items').glob('Group*.json')):
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        for item in data['items']:
            if 'name' not in item:
                continue  # Unnamed reserved entries are not translatable items.
            rows.append(('item', f"{data['group']},{item['number']}", str(path.relative_to(ROOT)), item['name']))
    path = ROOT / 'src/bin/Data/Monsters/Monsters.json'
    for monster in json.loads(path.read_text(encoding='utf-8-sig'))['monsters']:
        numbers = ','.join(str(n['number']) for n in monster['numbers'])
        rows.append((monster['kind'], numbers, str(path.relative_to(ROOT)), monster['name']))
        for number in monster['numbers']:
            if 'name' in number:
                rows.append((monster['kind'] + '-override', str(number['number']), str(path.relative_to(ROOT)), number['name']))
    for kind in sorted({r[0] for r in rows}):
        names = [r[3] for r in rows if r[0] == kind]
        counts[kind] = dict(total=len(names), translated=sum(bool(n.get('zh-CN')) for n in names),
                            missing=sum(not n.get('zh-CN') for n in names))
    write_tsv(directory, 'names.tsv', ['kind', 'ids', 'file', 'english', 'zh-CN'],
              [(kind, ids, file, names.get('en', ''), names.get('zh-CN', '')) for kind, ids, file, names in rows])
    return counts


def audit_source(directory):
    en = resources(ROOT / 'src/Localization/Game.en.resx')
    zh = resources(ROOT / 'src/Localization/Game.zh-CN.resx')
    keys = {identifier(k): k for k in en}
    refs, literals = [], []
    for path in sorted((ROOT / 'src/source').rglob('*')):
        if path.suffix not in ('.cpp', '.h'):
            continue
        file = path.relative_to(ROOT).as_posix()
        for line_no, line in enumerate(path.read_text(encoding='utf-8-sig', errors='replace').splitlines(), 1):
            for ref in re.findall(r'I18N::Game::(\w+)', line):
                key = keys.get(ref, '')
                refs.append((file, line_no, ref, key, en.get(key, ''), zh.get(key, '')))
            # Candidate inventory, deliberately not a claim that every string is UI.
            if line.lstrip().startswith('//'):
                continue
            for literal in re.findall(r'L"((?:[^"\\]|\\.)*)"', line):
                if re.search(r'[A-Za-z]{2}', literal):
                    literals.append((file, line_no, literal, line.strip()))
    write_tsv(directory, 'game-call-sites.tsv', ['file', 'line', 'identifier', 'key', 'english', 'zh-CN'], refs)
    write_tsv(directory, 'wide-literal-candidates.tsv', ['file', 'line', 'literal', 'context'], literals)
    helper = {r[3] for r in refs if '/MuHelper/' in r[0] or '/MUHelper/' in r[0] or r[0].endswith('/MuHelperBar.cpp')}
    helper.discard('')
    write_tsv(directory, 'helper.tsv', ['key', 'english', 'zh-CN'], [(k, en[k], zh.get(k, '')) for k in sorted(helper)])
    return dict(helper_keys=len(helper), helper_missing=sum(not zh.get(k) for k in helper),
                wide_literal_candidates=len(literals), wide_literal_files=len({r[0] for r in literals}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = dict(resources=audit_resources(args.output), names=audit_names(args.output), source=audit_source(args.output))
    (args.output / 'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
