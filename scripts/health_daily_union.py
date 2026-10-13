from __future__ import annotations
import argparse
import json
import re
from datetime import date as date_type
from pathlib import Path
from typing import Any
try:
    import yaml
except ModuleNotFoundError:
    yaml = None
TOTAL_KEYS = ('calories', 'fat_g', 'protein_g', 'carbs_g')

def _validate_date(value: str) -> None:
    try:
        date_type.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f'date must be YYYY-MM-DD, got {value!r}') from exc

def _parse_simple_frontmatter(fm_text: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    current_map: dict[str, Any] | None = None
    for raw in fm_text.splitlines():
        if not raw.strip():
            continue
        if raw.startswith('  ') and current_map is not None and (':' in raw):
            key, value = raw.strip().split(':', 1)
            current_map[key] = _parse_scalar(value.strip())
            continue
        current_map = None
        if ':' not in raw:
            continue
        key, value = raw.split(':', 1)
        key = key.strip()
        value = value.strip()
        if not value:
            parsed[key] = {}
            current_map = parsed[key]
        else:
            parsed[key] = _parse_scalar(value)
    return parsed

def _parse_scalar(value: str) -> Any:
    value = value.split('#', 1)[0].strip()
    if value in ('', 'null', 'None'):
        return None
    try:
        number = float(value)
    except ValueError:
        return value.strip('"\'')
    return int(number) if number.is_integer() else number

def _split_frontmatter(path: Path) -> tuple[dict[str, Any], str, str]:
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---'):
        raise ValueError(f'{path} is missing YAML frontmatter')
    parts = text.split('---', 2)
    if len(parts) != 3:
        raise ValueError(f'{path} has unclosed YAML frontmatter')
    fm = yaml.safe_load(parts[1]) if yaml is not None else _parse_simple_frontmatter(parts[1])
    fm = fm or {}
    if not isinstance(fm, dict):
        raise ValueError(f'{path} frontmatter must be a mapping')
    return (fm, parts[1], parts[2])

def _yaml_scalar(value: Any) -> str:
    if value is None:
        return '0'
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)

def _totals_from_frontmatter(fm: dict[str, Any], path: Path) -> dict[str, Any]:
    totals = fm.get('totals') or {}
    missing = [key for key in TOTAL_KEYS if key not in totals]
    if missing:
        raise ValueError(f'{path} frontmatter totals missing {missing}')
    return {key: totals[key] for key in TOTAL_KEYS}

def _strip_burn_lines(fm_text: str) -> str:
    lines = [line for line in fm_text.splitlines() if not re.match('^(burn_kcal|net_kcal|calories_burned):', line)]
    return '\n'.join(lines).rstrip() + '\n'

def _line_comment(fm_text: str, key: str) -> str:
    match = re.search(f'^{re.escape(key)}:\\s*[^#\\n]*(#.*)$', fm_text, re.M)
    return f'  {match.group(1).strip()}' if match else ''

def _extract_burn_from_fm(fm: dict[str, Any]) -> int | None:
    value = fm.get('burn_kcal')
    if value is None:
        value = fm.get('calories_burned')
    if value is None:
        return None
    return round(float(value))

def _load_food(repo_root: Path, day: str) -> tuple[dict[str, Any], str, str, bool]:
    food_path = repo_root / 'health' / 'logs' / 'food' / f'{day}.md'
    if food_path.exists():
        fm, fm_text, body = _split_frontmatter(food_path)
        return (fm, _strip_burn_lines(fm_text), body, False)
    legacy_path = repo_root / 'health' / 'logs' / 'daily' / f'{day}.md'
    if legacy_path.exists():
        fm, fm_text, body = _split_frontmatter(legacy_path)
        return (fm, _strip_burn_lines(fm_text), body, True)
    mode = 'maintenance'
    profile_path = repo_root / 'health' / 'profile.md'
    if profile_path.exists():
        try:
            profile_fm, _profile_fm_text, _profile_body = _split_frontmatter(profile_path)
            mode = profile_fm.get('mode', mode)
        except ValueError:
            pass
    fm = {'date': day, 'mode': mode, 'totals': {key: 0 for key in TOTAL_KEYS}}
    fm_text = f'\ndate: {day}\nmode: {mode}\ntotals:\n  calories: 0\n  fat_g: 0\n  protein_g: 0\n  carbs_g: 0\n'
    return (fm, fm_text, '\n## Meals\n', False)

def _load_burn_payload(repo_root: Path, day: str) -> dict[str, Any] | None:
    burn_path = repo_root / 'health' / 'logs' / 'burn' / f'{day}.md'
    if burn_path.exists():
        fm, _fm_text, _body = _split_frontmatter(burn_path)
        return fm
    legacy_json_path = repo_root / 'health' / 'logs' / 'burn' / f'{day}.json'
    if legacy_json_path.exists():
        return json.loads(legacy_json_path.read_text(encoding='utf-8'))
    return None

def _load_burn(repo_root: Path, day: str, legacy_fm: dict[str, Any] | None, legacy_fm_text: str | None) -> tuple[int | None, str, str | None]:
    payload = _load_burn_payload(repo_root, day)
    if payload is not None:
        if payload.get('burn_kcal') is None:
            return (None, '', None)
        burn = round(float(payload['burn_kcal']))
        partial = payload.get('partial')
        partial = partial is True or str(partial).lower() == 'yes'
        suffix = ' (partial day)' if partial else ''
        src = str(payload.get('source') or 'google-health-api').strip() or 'google-health-api'
        return (burn, f'  # {src}{suffix}', None)
    if legacy_fm is None:
        return (None, '', None)
    burn = _extract_burn_from_fm(legacy_fm)
    if burn is None:
        return (None, '', None)
    return (burn, _line_comment(legacy_fm_text or '', 'burn_kcal'), _line_comment(legacy_fm_text or '', 'net_kcal'))

def _render_daily(day: str, food_fm: dict[str, Any], food_body: str, burn: int | None, burn_comment: str, legacy_net_comment: str | None) -> str:
    totals = _totals_from_frontmatter(food_fm, Path(f'health/logs/food/{day}.md'))
    mode = food_fm.get('mode', 'maintenance')
    eaten = round(float(totals['calories']))
    net = eaten - burn if burn is not None else None
    out = ['---', f'date: {day}', f'mode: {mode}', 'totals:']
    out.extend((f'  {key}: {_yaml_scalar(totals[key])}' for key in TOTAL_KEYS))
    if burn is not None:
        out.append(f'burn_kcal: {burn}{burn_comment}')
        net_comment = legacy_net_comment or f'  # {eaten} eaten - {burn} burn'
        out.append(f'net_kcal: {net}{net_comment}')
    out.append('---')
    body = food_body
    if '## Meals' not in body:
        body = '\n## Meals\n' + body
    body = body.strip('\n')
    return '\n'.join(out) + '\n\n' + body + '\n'

def generate_daily(repo_root: Path | str, day: str) -> Path:
    repo_root = Path(repo_root)
    _validate_date(day)
    daily_path = repo_root / 'health' / 'logs' / 'daily' / f'{day}.md'
    food_path = repo_root / 'health' / 'logs' / 'food' / f'{day}.md'
    if not food_path.exists() and (not daily_path.exists()):
        return daily_path
    legacy_fm = legacy_fm_text = None
    if daily_path.exists():
        legacy_fm, legacy_fm_text, _legacy_body = _split_frontmatter(daily_path)
    food_fm, _food_fm_text, food_body, _food_from_legacy = _load_food(repo_root, day)
    burn, burn_comment, legacy_net_comment = _load_burn(repo_root, day, legacy_fm, legacy_fm_text)
    rendered = _render_daily(day, food_fm, food_body, burn, burn_comment, legacy_net_comment)
    daily_path.parent.mkdir(parents=True, exist_ok=True)
    daily_path.write_text(rendered, encoding='utf-8')
    return daily_path

def main(argv: list[str] | None=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--date', required=True)
    args = parser.parse_args(argv)
    path = generate_daily(Path(args.repo_root), args.date)
    print(f'generated {path}')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
