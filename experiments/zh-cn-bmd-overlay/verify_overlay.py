"""Read-only BMD overlay experiment; does not install or patch the client."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_legacy_text import fixed_names, quest_words

KINDS = {'skills': 50, 'quest-titles': 32, 'quest-words': 1024}
FILES = ('skill_eng.bmd', 'Quest_eng.bmd', 'QuestWords_eng.bmd')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def build_index(document):
    require(document['formatVersion'] == 1 and document['locale'] == 'zh-CN', 'Unknown overlay format/locale')
    require(set(document['sourceSha256']) == set(FILES), 'Unexpected source file set')
    entries = {}
    for entry in document['entries']:
        kind, number = entry['kind'], entry['id']
        require(kind in KINDS and type(number) is int and number >= 0, 'Invalid kind/ID')
        key = (kind, number)
        require(key not in entries, f'Duplicate ID: {key}')
        english, chinese = entry['english'], entry['zh-CN']
        require(isinstance(english, str) and isinstance(chinese, str) and english and chinese, 'Empty text')
        require('\0' not in chinese and '\0' not in english, 'Embedded NUL')
        require(len(chinese.encode('utf-16-le')) // 2 < KINDS[kind], f'Runtime text capacity: {key}')
        require(english.count(';') == chinese.count(';'), f'Paragraph separator mismatch: {key}')
        require('%' not in english and '%' not in chinese, 'MVP excludes formatting placeholders')
        require(entry.get('basis'), f'Missing mapping basis: {key}')
        entries[key] = entry
    return entries


def resolve(entries, kind, number, locale, original):
    """Pure display lookup: unknown IDs/locales/source text retain the original."""
    entry = entries.get((kind, number))
    if locale != 'zh-CN' or entry is None or original != entry['english']:
        return original
    return entry['zh-CN']


def read_sources(data_directory, expected_hashes):
    files = {name: data_directory / 'Local/Eng' / name for name in FILES}
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()}
    require(hashes == expected_hashes, 'BMD identity mismatch: refusing this asset version')
    inventories = {
        'skills': fixed_names(files['skill_eng.bmd'], 650, 108, 0, 50),
        'quest-titles': fixed_names(files['Quest_eng.bmd'], 200, 744, 6, 32),
        'quest-words': quest_words(files['QuestWords_eng.bmd']),
    }
    sources = {}
    for kind, rows in inventories.items():
        for number, original, encoding in rows:
            require((kind, number) not in sources, f'Duplicate source ID: {kind}/{number}')
            sources[(kind, number)] = (original, encoding)
    return sources, files, hashes


def check_mappings(entries, sources):
    previews = []
    for key, entry in entries.items():
        require(key in sources, f'Unknown source ID: {key}')
        original, encoding = sources[key]
        require(encoding == 'utf-8' and original == entry['english'], f'Source text mismatch: {key}')
        chinese = resolve(entries, *key, 'zh-CN', original)
        require(chinese == entry['zh-CN'], f'Chinese lookup failed: {key}')
        require(resolve(entries, *key, 'en', original) == original, f'English fallback failed: {key}')
        require(resolve(entries, *key, 'zh-CN', original + '!') == original + '!', 'Changed-source guard failed')
        previews.append({'kind': key[0], 'id': key[1], 'en': original, 'zh-CN': chinese})
    require(resolve(entries, 'skills', -1, 'zh-CN', 'Unknown') == 'Unknown', 'Missing-ID fallback failed')
    require(resolve(entries, 'skills', 4, 'de', 'Fire Ball') == 'Fire Ball', 'Other-locale fallback failed')
    return previews


def check_rejections(document):
    mutations = []
    duplicate = copy.deepcopy(document)
    duplicate['entries'].append(duplicate['entries'][0])
    mutations.append(duplicate)
    overflow = copy.deepcopy(document)
    overflow['entries'][0]['zh-CN'] = '字' * KINDS['skills']
    mutations.append(overflow)
    separators = copy.deepcopy(document)
    separators['entries'][-2]['zh-CN'] = '丢失段落分隔符'
    mutations.append(separators)
    for mutated in mutations:
        try:
            build_index(mutated)
        except ValueError:
            continue
        raise ValueError('Invalid overlay was accepted')
    return len(mutations)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(args.output.suffix.lower() == '.json', 'Output must be a JSON report')
    require(not args.output.resolve().is_relative_to(args.data.resolve()), 'Report must be outside the input Data directory')
    document = json.loads(Path(__file__).with_name('overlay.zh-CN.json').read_text(encoding='utf-8-sig'),
                          object_pairs_hook=unique_object)
    entries = build_index(document)
    sources, files, before = read_sources(args.data, document['sourceSha256'])
    previews = check_mappings(entries, sources)
    rejected = check_rejections(document)
    after = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()}
    require(before == after, 'BMD changed during validation')
    result = {'status': 'OFFLINE-VALIDATED; CLIENT-INTEGRATION-NOT-IMPLEMENTED; IN-GAME-NOT-TESTED',
              'entries': len(entries), 'negative_cases_rejected': rejected, 'bmd_unchanged': True,
              'sha256': after, 'previews': previews}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
