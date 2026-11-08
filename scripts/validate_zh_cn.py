"""Validate zh-CN format contracts and prove name-only JSON changes against v1.37.0."""
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from audit_zh_cn import ROOT, resources

PRINTF = re.compile(r'%(?:%|(?:\d+\$)?[-+ #0]*(?:\d+|\*)?(?:\.(?:\d+|\*))?(?:I64|I32|hh|ll|[hlLjztI])?[diuoxXfFeEgGaAcCsSpn])')


def original(path):
    return subprocess.check_output(['git', '-c', f'safe.directory={ROOT.as_posix()}', 'show',
                                    f'v1.37.0:{path.relative_to(ROOT).as_posix()}'], cwd=ROOT)


def strip_chinese(value):
    if isinstance(value, list):
        return [strip_chinese(v) for v in value]
    if isinstance(value, dict):
        return {k: strip_chinese(v) for k, v in value.items() if k != 'zh-CN'}
    return value


def check_resources(errors):
    added = {}
    for path in sorted((ROOT / 'src/Localization').glob('*.zh-CN.resx')):
        group = path.name.split('.')[0]
        en_path = path.with_name(group + '.en.resx')
        en, zh = resources(en_path), resources(path)
        entries = ET.parse(path).findall('data')
        if len(zh) != len(entries):
            errors.append(f'{path.name}: duplicate keys')
        if en_path.read_bytes().replace(b'\r\n', b'\n') != original(en_path).replace(b'\r\n', b'\n'):
            errors.append(f'{en_path.name}: English resource changed')
        old_path = ROOT / 'docs/localization-audit/baseline/summary.json'
        baseline_count = json.loads(old_path.read_text())['resources'][group]['translated']
        old = {}
        if baseline_count:
            old = {e.attrib['name']: e.findtext('value', '') for e in ET.fromstring(original(path)).findall('data')}
        for key, value in old.items():
            if zh.get(key) != value:
                errors.append(f'{path.name}: existing translation changed: {key}')
        for key, value in zh.items():
            if key not in en:
                errors.append(f'{path.name}: unknown key {key}')
                continue
            if key in old:
                continue
            if not value or '\ufffd' in value:
                errors.append(f'{path.name}: empty/corrupted value: {key}')
            if PRINTF.findall(en[key]) != PRINTF.findall(value) or en[key].count('%') != value.count('%'):
                errors.append(f'{path.name}: printf mismatch: {key}')
            for pattern in (r'\{\{?|\}\}?|\{\d+(?::[^}]+)?\}', r'(?<![\w:])/[A-Za-z]+', r'https?://[^\s<>]+', r'\\[nr]'):
                if re.findall(pattern, en[key]) != re.findall(pattern, value):
                    errors.append(f'{path.name}: protected tokens changed: {key}')
        added[group] = len(zh) - len(old)
    return added


def check_names(errors):
    additions = 0
    paths = list((ROOT / 'src/bin/Data/Items').glob('Group*.json'))
    paths.append(ROOT / 'src/bin/Data/Monsters/Monsters.json')
    for path in paths:
        after = json.loads(path.read_text(encoding='utf-8-sig'))
        before = json.loads(original(path))
        if strip_chinese(before) != strip_chinese(after):
            errors.append(f'{path.name}: non-zh-CN data changed')
        rows = after.get('items', after.get('monsters', []))
        old_rows = before.get('items', before.get('monsters', []))
        limit = 49 if 'items' in after else 64
        for row, old_row in zip(rows, old_rows):
            name = row.get('name', {}).get('zh-CN')
            old_name = old_row.get('name', {}).get('zh-CN')
            if old_name and name != old_name:
                errors.append(f'{path.name}: existing name changed')
            if name and not old_name:
                additions += 1
                if '||' in name or len(name.encode('utf-16-le')) // 2 > limit or '\ufffd' in name:
                    errors.append(f'{path.name}: invalid name {name}')
    return additions


def main():
    errors = []
    result = dict(resource_additions=check_resources(errors), name_additions=check_names(errors))
    # Font cmap validation supplements, but does not replace, visual UI testing.
    try:
        from fontTools.ttLib import TTFont
        text = ''.join(''.join(resources(p).values()) for p in (ROOT / 'src/Localization').glob('*.zh-CN.resx'))
        for path in (ROOT / 'src/bin/Data/Items').glob('Group*.json'):
            text += ''.join(i.get('name', {}).get('zh-CN', '') for i in json.loads(path.read_text(encoding='utf-8'))['items'])
        text += ''.join(i.get('name', {}).get('zh-CN', '') for i in json.loads((ROOT / 'src/bin/Data/Monsters/Monsters.json').read_text(encoding='utf-8'))['monsters'])
        fonts = ROOT / 'src/bin/fonts'
        overlay = json.loads((ROOT / 'src/bin/Data/Local/BmdText.zh-CN.json').read_text(encoding='utf-8'))
        text += ''.join(entry['zh-CN'] for entry in overlay['entries'])
        for filename in ['NotoSansSC-Regular.otf', 'NotoSansSC-Bold.otf']:
            with TTFont(fonts / filename) as font:
                missing = sorted({c for c in text if not c.isspace() and ord(c) not in font.getBestCmap()})
            if missing:
                errors.append(f'{filename}: missing glyphs {missing}')
        result['font_cmap'] = 'passed (regular and bold); visual rendering untested'
    except (ImportError, FileNotFoundError) as exc:
        result['font_cmap'] = f'not checked: {exc}'
        errors.append(f'Font validation unavailable: {exc}')
    result['errors'] = errors
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
