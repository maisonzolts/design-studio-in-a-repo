from pathlib import Path
import yaml
import re
from datetime import date, datetime
FRONTMATTER_DELIMITER = '---'

def parse_frontmatter(path: Path | str) -> dict:
    text = Path(path).read_text(encoding='utf-8')
    if not text.startswith(FRONTMATTER_DELIMITER):
        raise ValueError(f'missing frontmatter in {path}')
    parts = text.split(FRONTMATTER_DELIMITER, 2)
    if len(parts) < 3:
        raise ValueError(f'unclosed frontmatter in {path}')
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        raise ValueError(f'invalid YAML frontmatter in {path}: {e}') from e
    if not isinstance(fm, dict):
        raise ValueError(f'frontmatter must be a mapping in {path}')
    return fm

def parse_strict_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise TypeError(f'date must be a string or a date, got {type(value).__name__}')
    text = value.strip()
    if not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', text):
        raise ValueError(f'date must be written as YYYY-MM-DD, got {value!r}')
    return date.fromisoformat(text)
SOURCE_PATTERNS = {'usda': re.compile('^usda:(\\d+)$'), 'label_photo': re.compile('^label_photo:(health/label-photos/.+\\.(?:jpg|jpeg|png|heic|webp))$'), 'web': re.compile('^web:(https?://\\S+)\\s+@\\s+(\\d{4}-\\d{2}-\\d{2})$'), 'web_estimate': re.compile('^web_estimate:(\\S.*?)\\s+@\\s+(\\d{4}-\\d{2}-\\d{2})$'), 'owner_supplied': re.compile('^owner_supplied:(\\d{4}-\\d{2}-\\d{2})$'), 'recipe': re.compile('^recipe:(health/catalog/recipes/.+\\.md)$')}
LOW_CONFIDENCE_SOURCES = ('web_estimate', 'owner_supplied')

def validate_source_format(source) -> tuple[bool, str]:
    if source is None or source == '':
        return (False, 'source is blank or missing')
    if not isinstance(source, str):
        return (False, f'source must be a string, got {type(source).__name__}')
    for prefix, pattern in SOURCE_PATTERNS.items():
        if source.startswith(prefix + ':'):
            m = pattern.match(source)
            if not m:
                return (False, f"source has '{prefix}:' prefix but does not match required format")
            if prefix == 'usda':
                fdc_id = int(m.group(1))
                if fdc_id <= 0:
                    return (False, 'usda fdc_id must be a positive integer')
            elif prefix == 'web':
                date_str = m.group(2)
                try:
                    date.fromisoformat(date_str)
                except ValueError:
                    return (False, f'web source has invalid date: {date_str}')
            elif prefix == 'web_estimate':
                provenance, date_str = (m.group(1), m.group(2))
                if len(provenance.strip()) < 4:
                    return (False, 'web_estimate needs real provenance (the URL or the search query it came from), not a placeholder')
                if re.search('\\s+@\\s+', provenance):
                    return (False, "web_estimate provenance may not contain ' @ ' — that is the source's date separator and a second one makes the record ambiguous")
                try:
                    date.fromisoformat(date_str)
                except ValueError:
                    return (False, f'web_estimate has invalid date: {date_str}')
            elif prefix == 'owner_supplied':
                date_str = m.group(1)
                try:
                    date.fromisoformat(date_str)
                except ValueError:
                    return (False, f'owner_supplied has invalid date: {date_str}')
            return (True, '')
    return (False, f'source does not match any allowed prefix. Allowed: {sorted(SOURCE_PATTERNS.keys())}')

def validate_source_target(source: str, repo_root: Path | str) -> tuple[bool, str]:
    repo_root = Path(repo_root)
    if source.startswith('label_photo:'):
        rel = source[len('label_photo:'):]
        target = repo_root / rel
        try:
            resolved = target.resolve()
            allowed_root = (repo_root / 'health' / 'label-photos').resolve()
            if not resolved.is_relative_to(allowed_root):
                return (False, f'label_photo target escapes label-photos directory: {rel}')
        except (OSError, ValueError) as e:
            return (False, f'label_photo path resolution failed: {e}')
        if not target.exists():
            return (False, f'label_photo target not found: {rel}')
        if not target.is_file():
            return (False, f'label_photo target is not a file: {rel}')
        return (True, '')
    if source.startswith('recipe:'):
        rel = source[len('recipe:'):]
        target = repo_root / rel
        try:
            resolved = target.resolve()
            allowed_root = (repo_root / 'health' / 'catalog' / 'recipes').resolve()
            if not resolved.is_relative_to(allowed_root):
                return (False, f'recipe target escapes recipes directory: {rel}')
        except (OSError, ValueError) as e:
            return (False, f'recipe path resolution failed: {e}')
        if not target.exists():
            return (False, f'recipe target not found: {rel}')
        if not target.is_file():
            return (False, f'recipe target is not a file: {rel}')
        return (True, '')
    return (True, '')
ATWATER_TOLERANCE = 0.1
USDA_FIBER_ADJUSTED_TOLERANCE = 0.3
ATWATER_ABSOLUTE_FLOOR_CAL = 5.0
CALORIE_BASIS_USDA_FIBER_ADJUSTED = 'usda_fiber_adjusted'
CALORIE_BASIS_ATWATER_WITH_ETHANOL = 'atwater_with_ethanol'
CALORIE_BASIS_VALUES = {CALORIE_BASIS_USDA_FIBER_ADJUSTED, CALORIE_BASIS_ATWATER_WITH_ETHANOL}
ETHANOL_CAL_PER_G = 7.0

def validate_atwater(macros: dict, source: str | None=None) -> tuple[bool, str]:
    try:
        cal = float(macros['calories'])
        fat = float(macros['fat_g'])
        protein = float(macros['protein_g'])
        carbs = float(macros['carbs_g'])
    except (KeyError, TypeError, ValueError) as e:
        return (False, f'missing or invalid macro field: {e}')
    atwater = fat * 9 + protein * 4 + carbs * 4
    calorie_basis = macros.get('calorie_basis')
    tolerance = ATWATER_TOLERANCE
    if calorie_basis:
        if calorie_basis not in CALORIE_BASIS_VALUES:
            return (False, f'unknown calorie_basis: {calorie_basis}')
        if calorie_basis == CALORIE_BASIS_ATWATER_WITH_ETHANOL:
            try:
                ethanol = float(macros.get('ethanol_g'))
            except (KeyError, TypeError, ValueError):
                return (False, 'calorie_basis atwater_with_ethanol requires a numeric ethanol_g field - otherwise the alcohol calories are unaccounted')
            if ethanol <= 0:
                return (False, 'ethanol_g must be > 0 for atwater_with_ethanol')
            atwater += ethanol * ETHANOL_CAL_PER_G
        if calorie_basis == CALORIE_BASIS_USDA_FIBER_ADJUSTED:
            if not isinstance(source, str) or not source.startswith('usda:'):
                return (False, 'calorie_basis usda_fiber_adjusted is only valid for USDA sources')
            if cal > atwater:
                return (False, f'usda_fiber_adjusted calories must not exceed standard Atwater 4/4/9 sum: declared {cal:.1f} cal vs computed {atwater:.1f} cal')
            tolerance = USDA_FIBER_ADJUSTED_TOLERANCE
    if cal == 0 and atwater == 0:
        return (True, '')
    absolute_drift = abs(cal - atwater)
    if absolute_drift < ATWATER_ABSOLUTE_FLOOR_CAL:
        return (True, '')
    if cal == 0:
        return (False, f'atwater drift: 0 calories declared but macros sum to {atwater:.1f}')
    drift = absolute_drift / cal
    if drift > tolerance:
        return (False, f'atwater drift {drift * 100:.1f}% (>{tolerance * 100:.0f}%): declared {cal:.1f} cal vs computed {atwater:.1f} cal')
    return (True, '')
RECIPE_COMPUTED_TOLERANCE = 0.01
RECIPE_COMPUTED_ABSOLUTE_FLOOR = 0.5

def recipe_tree_has_fiber_adjusted(recipe_path: Path | str, repo_root: Path | str, _seen: set | None=None) -> bool:
    recipe_path = Path(recipe_path).resolve()
    repo_root = Path(repo_root)
    if _seen is None:
        _seen = set()
    if recipe_path in _seen:
        return False
    _seen.add(recipe_path)
    try:
        fm = parse_frontmatter(recipe_path)
    except (ValueError, OSError):
        return False
    for ing in fm.get('ingredients') or []:
        ref = ing.get('ref')
        if not ref:
            continue
        ing_path = repo_root / 'health' / ref
        try:
            ing_fm = parse_frontmatter(ing_path)
        except (ValueError, OSError):
            continue
        per_100g = ing_fm.get('per_100g')
        if isinstance(per_100g, dict) and per_100g.get('calorie_basis'):
            return True
        if ing_fm.get('calorie_basis'):
            return True
        if ing_fm.get('category') == 'recipe' and recipe_tree_has_fiber_adjusted(ing_path, repo_root, _seen):
            return True
    return False

def validate_recipe_declared_vs_computed(recipe_path: Path | str, repo_root: Path | str, declared: dict) -> tuple[bool, str]:
    try:
        computed = compute_recipe_macros(recipe_path, repo_root=repo_root)
    except (ValueError, KeyError, TypeError, OSError) as e:
        return (False, f'could not compute recipe macros: {e}')
    for key, comp_val in computed.items():
        try:
            decl_val = float(declared[key])
        except (KeyError, TypeError, ValueError) as e:
            return (False, f'missing or invalid macro field: {e}')
        allowed = max(RECIPE_COMPUTED_TOLERANCE * abs(comp_val), RECIPE_COMPUTED_ABSOLUTE_FLOOR)
        if abs(decl_val - comp_val) > allowed:
            return (False, f'declared {key} {decl_val} vs ingredient-computed {comp_val} (fiber-adjusted tree: declared macros must match computed)')
    return (True, '')

def compute_recipe_macros(recipe_path: Path | str, repo_root: Path | str) -> dict:
    recipe_path = Path(recipe_path)
    repo_root = Path(repo_root)
    fm = parse_frontmatter(recipe_path)
    yield_g = float(fm['yield_g'])
    if yield_g <= 0:
        raise ValueError(f'recipe yield_g must be positive: {recipe_path}')
    totals = {'calories': 0.0, 'fat_g': 0.0, 'protein_g': 0.0, 'carbs_g': 0.0}
    for ing in fm.get('ingredients', []):
        ref = ing['ref']
        grams = float(ing['grams'])
        ing_path = repo_root / 'health' / ref
        ing_fm = parse_frontmatter(ing_path)
        per_100g = ing_fm['per_100g']
        ratio = grams / 100.0
        for key in totals:
            totals[key] += ratio * float(per_100g[key])
    yield_ratio = yield_g / 100.0
    return {key: round(val / yield_ratio, 3) for key, val in totals.items()}

def validate_recipe(recipe_path: Path | str, repo_root: Path | str, _ancestors: frozenset | None=None) -> list[str]:
    recipe_path = Path(recipe_path)
    repo_root = Path(repo_root)
    errors: list[str] = []
    if _ancestors is None:
        _ancestors = frozenset()
    _ancestors = _ancestors | {recipe_path.resolve()}
    try:
        fm = parse_frontmatter(recipe_path)
    except ValueError as e:
        return [f'{recipe_path}: {e}']
    ingredients = fm.get('ingredients') or []
    if not ingredients:
        return [f'{recipe_path}: recipe has no ingredients (empty or missing)']
    for ing in ingredients:
        ref = ing.get('ref')
        if not ref:
            errors.append(f"{recipe_path}: ingredient missing 'ref' field")
            continue
        ing_path = repo_root / 'health' / ref
        if ing_path.exists() and ing_path.resolve() in _ancestors:
            errors.append(f'{recipe_path}: recipe cycle detected via {ref}')
            continue
        ing_errors = validate_file(ing_path, repo_root=repo_root, _ancestors=_ancestors)
        for e in ing_errors:
            errors.append(f'{recipe_path} → {e}')
    return errors

def validate_file(path: Path | str, repo_root: Path | str, _ancestors: frozenset | None=None) -> list[str]:
    path = Path(path)
    errors: list[str] = []
    if not path.exists():
        return [f'{path}: file does not exist']
    try:
        fm = parse_frontmatter(path)
    except ValueError as e:
        return [f'{path}: {e}']
    source = fm.get('source')
    valid_format, fmt_err = validate_source_format(source)
    if not valid_format:
        errors.append(f'{path}: {fmt_err}')
        return errors
    valid_target, tgt_err = validate_source_target(source, repo_root=repo_root)
    if not valid_target:
        errors.append(f'{path}: {tgt_err}')
    per_100g = fm.get('per_100g')
    if per_100g:
        top_level_calorie_basis = fm.get('calorie_basis')
        per_100g_calorie_basis = per_100g.get('calorie_basis')
        if top_level_calorie_basis and per_100g_calorie_basis and (top_level_calorie_basis != per_100g_calorie_basis):
            errors.append(f'{path}: conflicting calorie_basis values')
        macros = dict(per_100g)
        if top_level_calorie_basis and (not per_100g_calorie_basis):
            macros['calorie_basis'] = top_level_calorie_basis
        if fm.get('category') == 'recipe' and recipe_tree_has_fiber_adjusted(path, repo_root):
            ok, err = validate_recipe_declared_vs_computed(path, repo_root=repo_root, declared=macros)
        else:
            ok, err = validate_atwater(macros, source=source)
        if not ok:
            errors.append(f'{path}: per_100g {err}')
    if fm.get('category') == 'recipe':
        errors.extend(validate_recipe(path, repo_root=repo_root, _ancestors=_ancestors))
    return errors
import argparse
import sys
CATALOG_SUBDIRS = ['ingredients', 'products', 'recipes', 'restaurant']

def validate_catalog(health_dir: Path | str) -> list[str]:
    health_dir = Path(health_dir)
    repo_root = health_dir.parent
    errors: list[str] = []
    for subdir in CATALOG_SUBDIRS:
        cat_dir = health_dir / 'catalog' / subdir
        if not cat_dir.exists():
            continue
        for f in sorted(cat_dir.glob('*.md')):
            if f.name.startswith('.'):
                continue
            errors.extend(validate_file(f, repo_root=repo_root))
    return errors

def cli_main(argv: list[str] | None=None) -> int:
    parser = argparse.ArgumentParser(description='Anti-fabrication validator for health-coach catalog')
    parser.add_argument('--health-dir', default='health', help='path to the health/ data tree')
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors='replace')
        except (AttributeError, OSError):
            pass
    health_dir = Path(args.health_dir)
    if not health_dir.exists():
        print(f'ERROR: {health_dir} does not exist', file=sys.stderr)
        return 2
    errors = validate_catalog(health_dir)
    if not errors:
        print(f'OK: catalog at {health_dir} passed validation')
        return 0
    print(f'FAIL: {len(errors)} validation error(s) in {health_dir}:')
    for e in errors:
        print(f'  - {e}')
    return 1
if __name__ == '__main__':
    sys.exit(cli_main())
