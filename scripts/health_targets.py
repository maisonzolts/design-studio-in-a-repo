import re
from datetime import date
from pathlib import Path
import yaml

def bmr_female(weight_kg: float, height_cm: float, age: int) -> float:
    return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

def bmr_male(weight_kg: float, height_cm: float, age: int) -> float:
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5

def bmr_for_sex(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    key = str(sex or '').strip().lower()
    if key == 'female':
        return bmr_female(weight_kg, height_cm, age)
    if key == 'male':
        return bmr_male(weight_kg, height_cm, age)
    raise ValueError("profile sex must be 'female' or 'male' for Mifflin-St Jeor")

def tdee(bmr: float, activity_multiplier: float) -> float:
    return bmr * activity_multiplier
PREGNANCY_TRIMESTER_DELTAS = {'pregnancy_t1': 0, 'pregnancy_t2': 340, 'pregnancy_t3': 450}
VALID_MODES = {'maintenance', 'deficit'} | set(PREGNANCY_TRIMESTER_DELTAS.keys())

def calorie_target(tdee: float, mode: str, goal_rate_lb_per_week: float, pregnancy_ob_calories: float | None=None) -> float:
    if mode not in VALID_MODES:
        raise ValueError(f'unknown mode: {mode}. Valid: {sorted(VALID_MODES)}')
    if mode in PREGNANCY_TRIMESTER_DELTAS:
        if pregnancy_ob_calories is not None:
            return float(pregnancy_ob_calories)
        return tdee + PREGNANCY_TRIMESTER_DELTAS[mode]
    if mode == 'deficit':
        return tdee + goal_rate_lb_per_week * 500
    return tdee

def macro_split(calories: float, weight_lb: float, fat_floor_g: float, protein_floor_g_per_lb: float, protein_target_g_per_lb: float, carbs_g_target: float | None=None) -> dict:
    protein_target_g = round(weight_lb * protein_target_g_per_lb, 1)
    protein_floor_g = round(weight_lb * protein_floor_g_per_lb, 1)
    if carbs_g_target is None:
        fat_from_pct = 0.35 * calories / 9
        fat_g_target = round(max(fat_floor_g, fat_from_pct), 2)
        carbs_g = round((calories - protein_target_g * 4 - fat_g_target * 9) / 4, 3)
    else:
        carbs_g = round(float(carbs_g_target), 3)
        fat_g_target = round((calories - protein_target_g * 4 - carbs_g * 4) / 9, 2)
    return {'protein_target_g': protein_target_g, 'protein_floor_g': protein_floor_g, 'fat_g_target': fat_g_target, 'fat_g_floor': fat_floor_g, 'carbs_g': carbs_g, 'fat_below_safety_minimum': fat_g_target < fat_floor_g}

def compute_age(dob: date, reference: date | None=None) -> int:
    ref = reference or date.today()
    age = ref.year - dob.year
    if (ref.month, ref.day) < (dob.month, dob.day):
        age -= 1
    return age
FRONTMATTER_DELIMITER = '---'

def _split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith(FRONTMATTER_DELIMITER):
        raise ValueError("missing frontmatter: file must start with '---'")
    parts = text.split(FRONTMATTER_DELIMITER, 2)
    if len(parts) < 3:
        raise ValueError("missing frontmatter: file must have closing '---'")
    return (parts[1].strip(), parts[2].lstrip())

def read_profile(path: Path | str) -> dict:
    text = Path(path).read_text(encoding='utf-8')
    fm_yaml, _body = _split_frontmatter(text)
    profile = yaml.safe_load(fm_yaml)
    if not isinstance(profile, dict):
        raise ValueError('profile frontmatter must be a YAML mapping')
    return profile

def write_profile(path: Path | str, profile: dict) -> None:
    path = Path(path)
    body = ''
    if path.exists():
        try:
            existing = path.read_text(encoding='utf-8')
            _fm, body = _split_frontmatter(existing)
        except ValueError:
            body = ''
    fm_yaml = yaml.safe_dump(profile, sort_keys=False, allow_unicode=True).strip()
    new_text = f'{FRONTMATTER_DELIMITER}{fm_yaml}{FRONTMATTER_DELIMITER}\n{body}'
    path.write_text(new_text, encoding='utf-8')
LB_TO_KG = 0.453592

def recalculate(profile: dict, reference_date: date | None=None) -> dict:
    ref = reference_date or date.today()
    weight_lb = float(profile['current_weight_lb'])
    weight_kg = round(weight_lb * LB_TO_KG, 3)
    height_cm = float(profile['height_cm'])
    age = compute_age(profile['date_of_birth'], reference=ref)
    activity_mult = float(profile['activity_multiplier'])
    mode = profile['mode']
    goal_rate = float(profile.get('goal_rate_lb_per_week', 0) or 0)
    bmr = bmr_for_sex(profile.get('sex'), weight_kg=weight_kg, height_cm=height_cm, age=age)
    tdee_val = tdee(bmr=bmr, activity_multiplier=activity_mult)
    ob_overrides = profile.get('pregnancy_ob_overrides') or {}
    ob_calories = ob_overrides.get('calories')
    cal_target = calorie_target(tdee=tdee_val, mode=mode, goal_rate_lb_per_week=goal_rate, pregnancy_ob_calories=ob_calories)
    _carbs_target = profile.get('carbs_g_target')
    macros = macro_split(calories=cal_target, weight_lb=weight_lb, fat_floor_g=float(profile.get('fat_safety_minimum_g', 40)), protein_floor_g_per_lb=float(profile['protein_floor_g_per_lb']), protein_target_g_per_lb=float(profile['protein_target_g_per_lb']), carbs_g_target=None if _carbs_target in (None, '') else float(_carbs_target))
    updated = dict(profile)
    updated['current_weight_kg'] = weight_kg
    updated['bmr_kcal'] = round(bmr, 2)
    updated['tdee_kcal'] = round(tdee_val, 2)
    _fat_target = profile.get('fat_g_target')
    updated['daily_targets'] = {'calories': round(cal_target), 'protein_g_floor': macros['protein_floor_g'], 'protein_g_target': macros['protein_target_g'], 'carbs_g': macros['carbs_g'], 'fat_g_target': round(float(_fat_target), 1) if _fat_target not in (None, '') else macros['fat_g_target']}
    updated['weight_at_last_recalc_lb'] = weight_lb
    updated['last_recalculated'] = ref.isoformat()
    return updated
WEIGHT_DRIFT_THRESHOLD_LB = 2.0
STALENESS_DAYS = 30
_WEIGHT_ROW_RE = re.compile('^\\|\\s*(\\d{4}-\\d{2}-\\d{2})\\s*\\|\\s*(\\d+(?:\\.\\d+)?)\\s*\\|')

def weight_log_path(profile_path: Path | str) -> Path:
    return Path(profile_path).resolve().parent / 'logs' / 'weight.md'

def latest_logged_weight(weight_path: Path | str) -> tuple[str, float] | None:
    weight_path = Path(weight_path)
    if not weight_path.is_file():
        return None
    rows: list[tuple[str, float]] = []
    for line in weight_path.read_text(encoding='utf-8').splitlines():
        m = _WEIGHT_ROW_RE.match(line)
        if m:
            rows.append((m.group(1), float(m.group(2))))
    return max(rows) if rows else None

def should_recalculate(profile: dict, reference_date: date | None=None, weight_path: Path | str | None=None) -> bool:
    ref = reference_date or date.today()
    last_str = profile.get('last_recalculated')
    if not last_str:
        return True
    try:
        last = date.fromisoformat(str(last_str))
    except ValueError:
        return True
    if (ref - last).days > STALENESS_DAYS:
        return True
    baseline = profile.get('weight_at_last_recalc_lb')
    if baseline is None:
        return True
    current = None
    if weight_path is not None:
        logged = latest_logged_weight(weight_path)
        if logged is not None:
            current = logged[1]
    if current is None:
        current = profile.get('current_weight_lb')
    if current is None:
        return True
    if abs(float(current) - float(baseline)) > WEIGHT_DRIFT_THRESHOLD_LB:
        return True
    return False
import argparse
import sys

def cli_main(argv: list[str] | None=None) -> int:
    parser = argparse.ArgumentParser(description='Health targets calculator')
    parser.add_argument('--profile', default='health/profile.md', help='path to profile.md')
    parser.add_argument('--recalculate', action='store_true', help='force recalculation and write back')
    parser.add_argument('--check-staleness', action='store_true', help='recalculate only if needed (drift or staleness); exit 0 either way')
    parser.add_argument('--show', action='store_true', help='print current daily_targets without modifying anything')
    args = parser.parse_args(argv)
    profile_path = Path(args.profile)
    if not profile_path.exists():
        print(f'ERROR: profile not found at {profile_path}', file=sys.stderr)
        return 2
    profile = read_profile(profile_path)
    if args.show:
        targets = profile.get('daily_targets')
        if not targets:
            print('(no daily_targets — run --recalculate first)')
            return 1
        print(yaml.safe_dump(targets, sort_keys=False))
        return 0
    if args.check_staleness:
        wpath = weight_log_path(profile_path)
        if should_recalculate(profile, weight_path=wpath):
            logged = latest_logged_weight(wpath)
            if logged is not None:
                was = profile.get('current_weight_lb')
                if was is None or abs(float(was) - logged[1]) > 1e-09:
                    print(f'weight: {was} -> {logged[1]} (from weight.md {logged[0]})')
                profile['current_weight_lb'] = logged[1]
            updated = recalculate(profile)
            write_profile(profile_path, updated)
            print(f"recalculated: {updated['daily_targets']}")
        else:
            print('profile is fresh — no recalculation needed')
        return 0
    if args.recalculate:
        updated = recalculate(profile)
        write_profile(profile_path, updated)
        print(f"recalculated: {updated['daily_targets']}")
        return 0
    parser.print_help()
    return 1
if __name__ == '__main__':
    sys.exit(cli_main())
