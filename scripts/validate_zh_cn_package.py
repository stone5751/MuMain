"""Check the update allowlist, translated JSON provenance and CTest evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def validate(directory):
    allowed = re.compile(r'(?:Main\.exe|[^/]+\.dll|README\.zh-CN\.md|localization-build\.txt|ctest-results\.xml|shaders/[^/]+\.(?:spv|msl|dxil)|Data/Items/Group\d+_[A-Za-z]+\.json|Data/Monsters/Monsters\.json|Data/Local/BmdText\.zh-CN\.json)')
    files = sorted(p for p in directory.rglob('*') if p.is_file())
    names = {p.relative_to(directory).as_posix() for p in files}
    unexpected = sorted(name for name in names if not allowed.fullmatch(name))
    if unexpected:
        raise ValueError(f'Unexpected package entries: {unexpected}')
    required = {'Main.exe', 'MUnique.Client.Library.dll', 'localization-build.txt', 'README.zh-CN.md', 'ctest-results.xml'}
    if not required <= names or not any(n.startswith('shaders/') for n in names):
        raise ValueError('Missing required executable, library, shaders or build evidence')
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    metadata = (directory/'localization-build.txt').read_text(encoding='utf-8-sig')
    if f'source={source}' not in metadata or 'in-game-and-openmu-connection=NOT-TESTED' not in metadata:
        raise ValueError('Missing source identity or untested in-game status')
    suite = ET.parse(directory/'ctest-results.xml').getroot()
    tests = suite.findall('.//testcase')
    if not tests or suite.findall('.//failure') or suite.findall('.//error') or not any(t.find('skipped') is None for t in tests):
        raise ValueError('CTest report is empty, failed or entirely skipped')
    data_paths = subprocess.check_output(['git', 'diff', '--name-only', 'v1.37.0', 'HEAD', '--', 'src/bin/Data/Items', 'src/bin/Data/Monsters'], cwd=ROOT, text=True).splitlines()
    expected_data = {p.removeprefix('src/bin/') for p in data_paths}
    expected_data.add('Data/Local/BmdText.zh-CN.json')
    if {n for n in names if n.startswith('Data/')} != expected_data:
        raise ValueError('Packaged name files do not match the localized source changes')
    for name in expected_data:
        if json.loads((directory/name).read_text(encoding='utf-8-sig')) != json.loads((ROOT/'src/bin'/name).read_text(encoding='utf-8-sig')):
            raise ValueError(f'Packaged data differs from the build source: {name}')
    checksums = [hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(directory).as_posix() for p in files]
    (directory/'files.sha256').write_text('\n'.join(checksums)+'\n', encoding='utf-8')
    print(f'Validated {len(files)} package files; {len(tests)} CTest cases; no configuration or unrelated game assets. In-game tests: NOT TESTED.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    validate(parser.parse_args().directory)
