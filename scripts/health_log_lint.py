from __future__ import annotations
from pathlib import Path
from datetime import date
import re
import sys
sys.path.insert(0, str(Path(__file__).parent))
from health_validate import parse_frontmatter, parse_strict_date
MEAL_HEADING = re.compile('^### (\\d{2}):(\\d{2}) — .+')
ANY_H3 = re.compile('^### (.+)')
TOP_BULLET = re.compile('^-\\s+\\S')
CHILD_BULLET = re.compile('^\\s+-\\s+\\S')
MACRO_TAIL = re.compile('—\\s*~?([0-9.]+)\\s*cal,\\s*~?([0-9.]+)\\s*g?\\s*fat,\\s*~?([0-9.]+)\\s*g?\\s*protein,\\s*~?([0-9.]+)\\s*g?\\s*carbs')
CAL_ONLY = re.compile('—\\s*~?([0-9.]+)\\s*cal\\b')
SUMMARY_LINE = re.compile('^-?\\s*.{0,48}\\btotal\\b', re.I)
NOTE_LINE = re.compile('^-?\\s*(note:|\\*\\*|owner-estimated|macros not itemized|non-food:)', re.I)
NON_FOOD = ('steps', 'walk', 'tdee', 'burned', 'water', 'no macros', 'zero-macro', 'net deficit', 'non-food')
RECONCILE_TOL_PCT = 0.03
RECONCILE_TOL_CAL = 25.0

def _line_calories(text: str) -> float | None:
    m = MACRO_TAIL.search(text)
    if m and m.group(1) is not None:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None

def _completeness_issues(path: Path, fm: dict, text: str) -> list[str]:
    issues: list[str] = []
    body = text.split('---', 2)[2] if text.startswith('---') else text
    has_food = any((TOP_BULLET.match(ln) for ln in body.splitlines()))
    if not isinstance(fm.get('totals'), dict):
        if has_food:
            issues.append(f'{path.name}: has food lines but declares no `totals:` - nothing to reconcile against, so completeness cannot be verified')
        return issues
    lines = body.splitlines()
    total = 0.0
    i = 0
    while i < len(lines):
        raw = lines[i]
        if not TOP_BULLET.match(raw):
            i += 1
            continue
        stripped = raw.strip()
        kids: list[str] = []
        j = i + 1
        while j < len(lines) and (CHILD_BULLET.match(lines[j]) or not lines[j].strip()):
            if CHILD_BULLET.match(lines[j]):
                kids.append(lines[j].strip())
            j += 1
        if SUMMARY_LINE.match(stripped) or NOTE_LINE.match(stripped):
            i = j
            continue
        low = stripped.lower()
        cal = _line_calories(stripped)
        if cal is not None:
            total += cal
        else:
            kid_cals = [c for c in (_line_calories(k) for k in kids if not SUMMARY_LINE.match(k) and (not NOTE_LINE.match(k))) if c is not None]
            if kid_cals:
                total += sum(kid_cals)
            elif not any((k in low for k in NON_FOOD)):
                if CAL_ONLY.search(stripped):
                    total += float(CAL_ONLY.search(stripped).group(1))
                    issues.append(f"{path.name}: food line has calories but not all four macros: '{stripped[:70]}'")
                else:
                    issues.append(f"{path.name}: food line carries no macros: '{stripped[:70]}'")
        i = j
    declared = None
    totals = fm.get('totals')
    if isinstance(totals, dict):
        try:
            declared = float(totals.get('calories'))
        except (TypeError, ValueError):
            declared = None
    if declared is not None and total > 0:
        drift = abs(total - declared)
        if drift > max(RECONCILE_TOL_CAL, declared * RECONCILE_TOL_PCT):
            issues.append(f'{path.name}: line items do not reconcile to totals — declared {declared:.0f} cal, lines sum to {total:.0f} (drift {total - declared:+.0f})')
    return issues

def lint_log(path: Path | str, today: date | None=None) -> tuple[list[str], list[str]]:
    path = Path(path)
    today = today or date.today()
    hard: list[str] = []
    warn: list[str] = []
    try:
        fm = parse_frontmatter(path)
    except ValueError as e:
        return ([f'{path.name}: {e}'], [])
    fm_date = fm.get('date')
    try:
        fm_date_parsed = parse_strict_date(fm_date) if fm_date is not None else None
    except (ValueError, TypeError):
        fm_date_parsed = None
    stem = path.stem
    file_date = None
    try:
        file_date = date.fromisoformat(stem)
    except ValueError:
        pass
    issues: list[str] = []
    if file_date is None:
        issues.append(f'{path.name}: filename is not an ISO date')
    if fm_date_parsed is not None and file_date is not None and (fm_date_parsed != file_date):
        issues.append(f'{path.name}: frontmatter date {fm_date_parsed} != filename {file_date}')
    text = path.read_text(encoding='utf-8')
    times: list[int] = []
    for line in text.splitlines():
        m3 = ANY_H3.match(line)
        if not m3:
            continue
        mh = MEAL_HEADING.match(line)
        if not mh:
            issues.append(f"{path.name}: non-HH:MM meal heading: '{line.strip()}'")
            continue
        hh, mm = (int(mh.group(1)), int(mh.group(2)))
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            issues.append(f"{path.name}: invalid clock time in heading: '{line.strip()}'")
            continue
        times.append(hh * 60 + mm)
    if times != sorted(times):
        issues.append(f'{path.name}: meal headings not in ascending time order')
    issues.extend(_completeness_issues(path, fm, text))
    is_new = file_date is not None and file_date >= today
    if is_new:
        hard.extend(issues)
    else:
        warn.extend(issues)
    return (hard, warn)

def lint_daily_dir(daily_dir: Path | str, today: date | None=None, strict: bool=False):
    daily_dir = Path(daily_dir)
    hard: list[str] = []
    warn: list[str] = []
    for f in sorted(daily_dir.glob('*.md')):
        h, w = lint_log(f, today=today)
        if strict:
            hard.extend(h + w)
        else:
            hard.extend(h)
            warn.extend(w)
    return (hard, warn)

def cli_main(argv: list[str] | None=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description='Structural linter for health daily logs')
    p.add_argument('--daily-dir', default='health/logs/daily')
    p.add_argument('--strict', action='store_true', help='treat all violations as hard failures')
    args = p.parse_args(argv)
    d = Path(args.daily_dir)
    if not d.exists():
        print(f'ERROR: {d} does not exist', file=sys.stderr)
        return 2
    hard, warn = lint_daily_dir(d, strict=args.strict)
    for w in warn:
        print(f'  WARN: {w}')
    for h in hard:
        print(f'  FAIL: {h}')
    if hard:
        print(f'FAIL: {len(hard)} hard structural issue(s)')
        return 1
    print(f'OK: {len(warn)} warning(s), 0 hard issues')
    return 0
if __name__ == '__main__':
    sys.exit(cli_main())
