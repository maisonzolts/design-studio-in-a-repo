import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from health_validate import parse_frontmatter
REPO = Path(__file__).resolve().parent.parent

def calc(recipe_path):
    fm = parse_frontmatter(recipe_path)
    totals = {'calories': 0.0, 'fat_g': 0.0, 'protein_g': 0.0, 'carbs_g': 0.0}
    print(f"\n{fm.get('name', recipe_path)}")
    print('-' * 60)
    for ing in fm.get('ingredients', []):
        ref, grams = (ing['ref'], float(ing['grams']))
        ip = REPO / 'health' / ref
        ifm = parse_frontmatter(ip)
        p = ifm['per_100g']
        r = grams / 100.0
        c = {k: r * float(p[k]) for k in totals}
        for k in totals:
            totals[k] += c[k]
        print(f"  {grams:6.0f}g  {ifm['name'][:34]:34}  {c['calories']:5.0f} cal  {c['protein_g']:4.1f}P  {c['fat_g']:4.1f}F  {c['carbs_g']:4.1f}C")
    print('-' * 60)
    print(f"  MEAL TOTAL:  {totals['calories']:.0f} cal  {totals['protein_g']:.1f}P  {totals['fat_g']:.1f}F  {totals['carbs_g']:.1f}C")
    yield_g = float(fm.get('yield_g', sum((float(i['grams']) for i in fm['ingredients']))))
    yr = yield_g / 100.0
    per100 = {k: round(v / yr, 3) for k, v in totals.items()}
    print(f'  yield_g: {yield_g:.0f}')
    print(f"  per_100g:  calories: {per100['calories']}  fat_g: {per100['fat_g']}  protein_g: {per100['protein_g']}  carbs_g: {per100['carbs_g']}")
    return (totals, per100)
if __name__ == '__main__':
    for path in sys.argv[1:]:
        calc(path)
