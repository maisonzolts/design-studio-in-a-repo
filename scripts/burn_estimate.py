from __future__ import annotations
import statistics as st
from pathlib import Path
MIN_SUPPORTED_STEPS = 500
K_NEIGHBOURS = 15

def load_ledger_days(ledger_path: Path | str) -> list[dict]:
    header: list[str] = []
    days: list[dict] = []
    for line in Path(ledger_path).read_text(encoding='utf-8').splitlines():
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if cells and cells[0] == 'date':
            header = cells
            continue
        if not header or set(cells[0]) <= set('-: '):
            continue
        row = dict(zip(header, cells))
        if row.get('partial') != 'no':
            continue
        if row.get('suspect') in ('yes', 'est'):
            continue

        def num(key):
            v = row.get(key)
            if v in (None, '', '—', '-'):
                return None
            try:
                return float(v)
            except ValueError:
                return None
        burn, steps = (num('burn_kcal'), num('steps'))
        if burn is None or steps is None:
            continue
        days.append({'date': row['date'], 'burn': burn, 'steps': steps, 'active': num('active_min')})
    return days

def _ols(days: list[dict], steps: float) -> float:
    xs = [d['steps'] for d in days]
    ys = [d['burn'] for d in days]
    mx, my = (st.mean(xs), st.mean(ys))
    denom = sum(((x - mx) ** 2 for x in xs))
    if denom == 0:
        return my
    k = sum(((x - mx) * (y - my) for x, y in zip(xs, ys))) / denom
    return my - k * mx + k * steps

def _neighbours(days: list[dict], steps: float, active_min: float | None, k: int) -> list[dict]:
    if active_min is None:
        return sorted(days, key=lambda d: abs(d['steps'] - steps))[:k]
    pool = [d for d in days if d.get('active') is not None]
    if len(pool) < k:
        return sorted(days, key=lambda d: abs(d['steps'] - steps))[:k]
    return sorted(pool, key=lambda d: abs(d['steps'] - steps) / 1000.0 + abs(d['active'] - active_min) / 60.0)[:k]

def _loo_error(days: list[dict], active_min: float | None) -> tuple[float, float]:
    errs = []
    for i, d in enumerate(days):
        train = days[:i] + days[i + 1:]
        if not train:
            continue
        if active_min is None or d.get('active') is None:
            pred = _ols(train, d['steps'])
        else:
            near = _neighbours(train, d['steps'], d['active'], K_NEIGHBOURS)
            pred = st.median([t['burn'] for t in near])
        errs.append(abs(pred - d['burn']))
    if not errs:
        return (0.0, 0.0)
    errs.sort()
    return (st.mean(errs), errs[min(int(0.9 * len(errs)), len(errs) - 1)])

def estimate_burn(ledger_path: Path | str, steps: float, active_min: float | None=None) -> dict:
    steps = float(steps)
    if steps < MIN_SUPPORTED_STEPS:
        raise ValueError(
            f"{steps:.0f} steps is below the supported floor of "
            f"{MIN_SUPPORTED_STEPS}; log no burn rather than inventing one."
        )
    if active_min is not None:
        active_min = float(active_min)
        if active_min < 0:
            raise ValueError('active_min cannot be negative')
    days = load_ledger_days(ledger_path)
    if len(days) < 30:
        raise ValueError(f'only {len(days)} usable days in the ledger; need at least 30 before an estimate means anything')
    observed_max = max((d['steps'] for d in days))
    if steps > observed_max * 1.25:
        raise ValueError(
            f"{steps:.0f} steps is far beyond the highest recorded day "
            f"({observed_max:.0f}); verify the input instead of extrapolating."
        )
    if active_min is None:
        value = _ols(days, steps)
        method = "linear regression on steps from private measured history"
    else:
        near = _neighbours(days, steps, active_min, K_NEIGHBOURS)
        value = st.median([d['burn'] for d in near])
        method = f"median of {len(near)} similar measured days (steps + active minutes)"
    mae, p90 = _loo_error(days, active_min)
    return {'burn_kcal': int(round(value)), 'method': method, 'n_days': len(days), 'mae': int(round(mae)), 'p90_error': int(round(p90)), 'low': int(round(value - p90)), 'high': int(round(value + p90)), 'estimated': True, 'confidence': 'medium' if active_min is not None else 'low', 'caveat': "This is an ESTIMATE from private measured history, not a measurement. Exclude it from TDEE and maintenance calculations."}
if __name__ == '__main__':
    import argparse
    import json
    ROOT = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--steps', type=float, required=True)
    ap.add_argument('--active-min', type=float, default=None)
    ap.add_argument('--ledger', default=str(ROOT / 'health' / 'logs' / 'burn-ledger.md'))
    a = ap.parse_args()
    print(json.dumps(estimate_burn(a.ledger, a.steps, a.active_min), indent=2))
