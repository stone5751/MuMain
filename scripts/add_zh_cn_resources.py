"""Append reviewed key<TAB>translation rows, refusing unknown or duplicate keys."""
import argparse
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr
from audit_zh_cn import ROOT, resources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('group', choices=['Game', 'Dialog'])
    parser.add_argument('translations', type=Path)
    args = parser.parse_args()
    source = ROOT / 'src/Localization' / f'{args.group}.en.resx'
    target = source.with_name(f'{args.group}.zh-CN.resx')
    en, zh = resources(source), resources(target)
    text = target.read_text(encoding='utf-8') if target.exists() else source.read_text(encoding='utf-8').split('  <data ')[0] + '</root>\n'
    entries, seen = [], set()
    for row in args.translations.read_text(encoding='utf-8-sig').splitlines():
        if not row or row.startswith('#'):
            continue
        key, value = row.split('\t', 1)
        if key not in en or key in seen or not value:
            raise ValueError(f'Unknown/duplicate key or empty value: {key}')
        seen.add(key)
        if key in zh:
            if zh[key] != value:
                raise ValueError(f'Refusing to replace existing translation: {key}')
            continue
        entries.append(f'  <data name={quoteattr(key)} xml:space="preserve">\n    <value>{escape(value)}</value>\n  </data>\n')
    target.write_text(text.replace('</root>', ''.join(entries) + '</root>'), encoding='utf-8', newline='\n')
    print(f'{target.name}: added {len(entries)} entries')


if __name__ == '__main__':
    main()
