from pathlib import Path
import json
import os
import urllib.parse
import urllib.request
USDA_BASE_URL = 'https://api.nal.usda.gov/fdc/v1'

def load_dotenv(path: Path | str='.env') -> int:
    p = Path(path)
    if not p.exists():
        return 0
    count = 0
    for raw_line in p.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        key, _, value = line.partition('=')
        key = key.strip()
        if not key or not key.replace('_', '').isalnum():
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and (value[0] in ('"', "'")):
            value = value[1:-1]
        if key not in os.environ:
            os.environ[key] = value
            count += 1
    return count
NUTRIENT_CALORIES = 1008
NUTRIENT_FAT = 1004
NUTRIENT_PROTEIN = 1003
NUTRIENT_CARBS = 1005

def _http_get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode('utf-8'))

def _extract_nutrient(food: dict, nutrient_id: int) -> float:
    for n in food.get('foodNutrients', []):
        if n.get('nutrientId') == nutrient_id:
            return float(n.get('value', 0))
    return 0.0

def search_usda(query: str, api_key: str, page_size: int=5) -> list[dict]:
    params = urllib.parse.urlencode({'query': query, 'pageSize': page_size, 'api_key': api_key})
    url = f'{USDA_BASE_URL}/foods/search?{params}'
    data = _http_get_json(url)
    results = []
    for food in data.get('foods', []):
        results.append({'fdc_id': food['fdcId'], 'description': food.get('description', ''), 'data_type': food.get('dataType', ''), 'per_100g': {'calories': _extract_nutrient(food, NUTRIENT_CALORIES), 'fat_g': _extract_nutrient(food, NUTRIENT_FAT), 'protein_g': _extract_nutrient(food, NUTRIENT_PROTEIN), 'carbs_g': _extract_nutrient(food, NUTRIENT_CARBS)}})
    return results
CACHE_HEADER = "# USDA FoodData Central — Local Cache\n\nThis file is automatically managed by `health_usda.py`. It stores results from the\nUSDA API so we don't re-hit the network for foods we've already looked up.\n\nFormat: one row per cached food, pipe-delimited.\n\n| fdc_id | description | calories | fat_g | protein_g | carbs_g |\n|---|---|---|---|---|---|\n"

def _read_cache(cache_path: Path) -> dict[int, dict]:
    if not cache_path.exists():
        return {}
    cache: dict[int, dict] = {}
    text = cache_path.read_text(encoding='utf-8')
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith('|'):
            continue
        if 'fdc_id' in line or set(line.replace('|', '').strip()) == {'-'}:
            continue
        parts = [p.strip() for p in line.strip('|').split('|')]
        if len(parts) != 6:
            continue
        try:
            fdc_id = int(parts[0])
            cache[fdc_id] = {'fdc_id': fdc_id, 'description': parts[1], 'per_100g': {'calories': float(parts[2]), 'fat_g': float(parts[3]), 'protein_g': float(parts[4]), 'carbs_g': float(parts[5])}}
        except (ValueError, IndexError):
            continue
    return cache

def _write_cache(cache_path: Path, cache: dict[int, dict]) -> None:
    lines = [CACHE_HEADER]
    for fdc_id in sorted(cache.keys()):
        entry = cache[fdc_id]
        p = entry['per_100g']
        lines.append(f"| {fdc_id} | {entry['description']} | {p['calories']} | {p['fat_g']} | {p['protein_g']} | {p['carbs_g']} |")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

def cache_get(cache_path: Path | str, fdc_id: int) -> dict | None:
    cache = _read_cache(Path(cache_path))
    return cache.get(int(fdc_id))

def cache_set(cache_path: Path | str, fdc_id: int, description: str, per_100g: dict) -> None:
    cache_path = Path(cache_path)
    cache = _read_cache(cache_path)
    cache[int(fdc_id)] = {'fdc_id': int(fdc_id), 'description': description, 'per_100g': per_100g}
    _write_cache(cache_path, cache)
import re
from datetime import date

def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub('[^a-z0-9]+', '-', text)
    return text.strip('-')

def generate_catalog_entry(usda_result: dict, out_dir: Path | str) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = _slugify(usda_result['description'])
    fdc_id = usda_result['fdc_id']
    p = usda_result['per_100g']
    content = f"---\nname: {usda_result['description']}\nslug: {slug}\ncategory: ingredient\nsource: usda:{fdc_id}\nper_100g:\n  calories: {p['calories']}\n  fat_g: {p['fat_g']}\n  protein_g: {p['protein_g']}\n  carbs_g: {p['carbs_g']}\nnotes: USDA {usda_result.get('data_type', 'FoodData Central')} reference\nlast_updated: {date.today().isoformat()}\n---\n"
    out_path = out_dir / f'{slug}.md'
    out_path.write_text(content, encoding='utf-8')
    return out_path
import argparse
import sys

def cli_main(argv: list[str] | None=None) -> int:
    parser = argparse.ArgumentParser(description='USDA FoodData Central lookup')
    parser.add_argument('--search', help='search query string')
    parser.add_argument('--max-results', type=int, default=5)
    parser.add_argument('--cache', default='health/.cache/usda.md', help='path to local cache file')
    parser.add_argument('--save-as-ingredient', type=int, metavar='FDC_ID', help='after search, save the matching fdc_id as an ingredient catalog file')
    parser.add_argument('--ingredients-dir', default='health/catalog/ingredients')
    args = parser.parse_args(argv)
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
    api_key = os.environ.get('USDA_API_KEY')
    if not api_key:
        print('ERROR: USDA_API_KEY not set in environment. Sign up for a free key at https://fdc.nal.usda.gov/api-key-signup.html', file=sys.stderr)
        return 2
    if not args.search:
        parser.print_help()
        return 1
    results = search_usda(args.search, api_key=api_key, page_size=args.max_results)
    if not results:
        print(f'No results for {args.search!r}')
        return 0
    print(f'Found {len(results)} result(s) for {args.search!r}:\n')
    for r in results:
        p = r['per_100g']
        print(f"  fdc_id={r['fdc_id']:>8} | {r['description']:<40} | {p['calories']} cal | {p['fat_g']}g fat | {p['protein_g']}g protein | {p['carbs_g']}g carbs")
        cache_set(args.cache, r['fdc_id'], r['description'], r['per_100g'])
    if args.save_as_ingredient:
        match = next((r for r in results if r['fdc_id'] == args.save_as_ingredient), None)
        if not match:
            print(f"\nERROR: fdc_id {args.save_as_ingredient} not in this search's results", file=sys.stderr)
            return 1
        out_path = generate_catalog_entry(match, out_dir=args.ingredients_dir)
        print(f'\nSaved as ingredient: {out_path}')
    return 0
if __name__ == '__main__':
    sys.exit(cli_main())
