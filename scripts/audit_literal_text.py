"""Supplement the wide-literal audit with narrow C++ and RML candidates.

These heuristic counts include identifiers, diagnostics and false positives;
they must not be reported as counts of untranslated user interface messages.
"""
import argparse
import json
import re
from pathlib import Path

from audit_zh_cn import ROOT, write_tsv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    narrow_count, narrow_ui, rml = 0, [], []
    display_call = re.compile(r'ImGui::|Set(?:Text|Title|Label)|RenderText|DrawText|MessageBox|SetInnerRML|AddText|AddButton')
    for path in sorted((ROOT / 'src').rglob('*')):
        if path.suffix not in ('.cpp', '.h', '.rml'):
            continue
        for line_no, line in enumerate(path.read_text(encoding='utf-8-sig', errors='replace').splitlines(), 1):
            if line.lstrip().startswith(('//', '#include', '<!--')):
                continue
            file = path.relative_to(ROOT).as_posix()
            if path.suffix == '.rml':
                for literal in re.findall(r'>([^<>]+)<', line):
                    literal = re.sub(r'\{\{.*?\}\}', '', literal).strip()
                    if re.search('[A-Za-z]{2}', literal):
                        rml.append((file, line_no, literal, line.strip()))
            else:
                for literal in re.findall(r'(?<![A-Za-z0-9_])"((?:[^"\\]|\\.)*)"', line):
                    if re.search('[A-Za-z]{2}', literal):
                        narrow_count += 1
                        if display_call.search(line):
                            narrow_ui.append((file, line_no, literal, line.strip()))
    columns = ['file', 'line', 'literal', 'context']
    write_tsv(args.output, 'narrow-display-candidates.tsv', columns, narrow_ui)
    write_tsv(args.output, 'rml-text-candidates.tsv', columns, rml)
    result = dict(narrow_literal_candidates=narrow_count, narrow_display_candidates=len(narrow_ui),
                  rml_text_candidates=len(rml),
                  limitation='Heuristic inventory, not a count of missing translations. Multiline strings, comments, macros and data bindings need manual classification.')
    (args.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
