#!/usr/bin/env python3
"""Redistribute religion fractions for specific cultures in 06_pops.txt.

Usage:
  python tools/redistribute_religions.py [--apply] [--verbose]

By default the script does a dry-run; use `--apply` to write changes and
create a unique backup (`.bak`, `.bak2`, ...).
"""
from pathlib import Path
import argparse
import re
import shutil
from typing import Tuple


INPUT = Path("main_menu/setup/start/06_pops.txt")


def unique_backup(path: Path) -> Path:
    base = path.with_suffix('.bak')
    if not base.exists():
        return base
    i = 2
    while True:
        cand = path.with_suffix(f'.bak{i}')
        if not cand.exists():
            return cand
        i += 1


RULES = {
    'korean_culture': {
        'nobles': {'sanjiao': 1.00},
        'clergy': {'mahayana': 1.00},
        'burghers': {'mahayana': 0.70, 'sanjiao': 0.30},
        'peasants': {'mahayana': 0.85, 'sanjiao': 0.15},
    },
    'tamna_culture': {
        'elites': {'sanjiao': 0.50, 'mahayana': 0.50},
        'clergy': {'mahayana': 1.00},
        'burghers': {'mahayana': 0.90, 'sanjiao': 0.10},
        'peasants': {'mahayana': 0.90, 'sanjiao': 0.10},
    },
}


# Match the whole define_pop block contents and capture the inner text
RE = re.compile(r"(?P<indent>\s*)define_pop\s*=\s*\{(?P<inner>[^}]*)\}")


def parse_inner(inner: str) -> dict:
    # parse key = value pairs inside define_pop
    pairs = re.findall(r"(\w+)\s*=\s*([^\s]+)", inner)
    return {k: v for k, v in pairs}


def make_replacement(ptype: str, size: float, culture: str) -> Tuple[list, int]:
    # returns replacement list of (religion, amount) and count
    if culture not in RULES:
        return None, 0
    rules = RULES[culture]
    key = ptype if ptype in rules else ptype.lower()
    if key not in rules:
        return None, 0
    fractions = rules[key]
    raws = [(relig, size * frac) for relig, frac in fractions.items()]
    rounded = [round(v, 3) for _, v in raws]
    resid = round(size - sum(rounded), 3)
    if rounded and abs(resid) >= 0.001:
        rounded[0] = round(rounded[0] + resid, 3)
    lines = []
    for (relig, _), r in zip(raws, rounded):
        if r <= 0:
            continue
        lines.append((relig, r))
    return lines, len(lines)


def repl(m: re.Match) -> str:
    indent = m.group('indent')
    inner = m.group('inner')
    parsed = parse_inner(inner)
    ptype = parsed.get('type')
    size_s = parsed.get('size')
    culture = parsed.get('culture')
    if not (ptype and size_s and culture):
        return m.group(0)
    try:
        size = float(size_s)
    except ValueError:
        return m.group(0)
    repl_lines, _ = make_replacement(ptype, size, culture)
    if not repl_lines:
        return m.group(0)
    out = []
    for relig, r in repl_lines:
        out.append(f"{indent}define_pop = {{ type = {ptype} size = {r:.3f} culture = {culture} religion = {relig} }}")
    return '\n'.join(out)


def analyze(text: str) -> Tuple[str, int]:
    new_text, count = RE.subn(repl, text)
    return new_text, count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='write changes and create backup')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    if not INPUT.exists():
        print('Input file not found:', INPUT)
        return
    text = INPUT.read_text()
    new_text, count = analyze(text)
    if count == 0 or new_text == text:
        print('No changes required')
        return
    print(f'Replacements to make: {count}')
    if args.verbose:
        print('Dry-run sample (first 40 lines of changes):')
        old_lines = text.splitlines()
        new_lines = new_text.splitlines()
        shown = 0
        for o, n in zip(old_lines, new_lines):
            if o != n:
                print('- ' + o)
                print('+ ' + n)
                shown += 1
            if shown >= 40:
                break
    if not args.apply:
        print('Dry-run complete. Rerun with --apply to write changes.')
        return
    bak = unique_backup(INPUT)
    shutil.copy2(INPUT, bak)
    INPUT.write_text(new_text)
    print(f'Applied {count} replacements; backup saved at {bak}')


if __name__ == '__main__':
    main()
