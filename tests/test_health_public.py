from pathlib import Path
from datetime import date, timedelta
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "health-app"))

from health_validate import validate_catalog, validate_source_format
from health_targets import bmr_female, bmr_for_sex, bmr_male, calorie_target
from health_log_lint import lint_log
from health_daily_union import generate_daily
from burn_estimate import estimate_burn
import health_usda
from server.main import healthz


def test_synthetic_catalog_validates():
    assert validate_catalog(ROOT / "health") == []


def test_source_enum_rejects_unknown_values():
    ok, _ = validate_source_format("memory:trust-me")
    assert not ok


def test_target_math_is_deterministic():
    assert bmr_female(60, 165, 30) == 1320.25
    assert bmr_male(60, 165, 30) == 1486.25
    assert bmr_for_sex("female", 60, 165, 30) == 1320.25
    assert bmr_for_sex("male", 60, 165, 30) == 1486.25
    try:
        bmr_for_sex("", 60, 165, 30)
    except ValueError:
        pass
    else:
        raise AssertionError("missing sex must not default to one body")
    assert calorie_target(2000, "maintenance", 0) == 2000


def test_health_api_imports_and_reports_ready():
    assert healthz() == {"status": "ok"}


def test_daily_log_linter_accepts_reconciled_synthetic_day(tmp_path):
    log = tmp_path / "2099-01-01.md"
    log.write_text(
        """---
date: 2099-01-01
totals:
  calories: 100
  fat_g: 0
  protein_g: 0
  carbs_g: 25
---

### 08:00 — breakfast
- synthetic food — 100 cal, 0g fat, 0g protein, 25g carbs
""",
        encoding="utf-8",
    )
    assert lint_log(log, today=date(2099, 1, 1)) == ([], [])


def test_daily_union_combines_food_and_burn_sources(tmp_path):
    food = tmp_path / "health" / "logs" / "food" / "2099-01-01.md"
    burn = tmp_path / "health" / "logs" / "burn" / "2099-01-01.md"
    food.parent.mkdir(parents=True)
    burn.parent.mkdir(parents=True)
    food.write_text(
        """---
date: 2099-01-01
mode: maintenance
totals:
  calories: 100
  fat_g: 0
  protein_g: 0
  carbs_g: 25
---

## Meals
""",
        encoding="utf-8",
    )
    burn.write_text(
        """---
date: 2099-01-01
burn_kcal: 150
source: synthetic-fixture
---
""",
        encoding="utf-8",
    )
    output = generate_daily(tmp_path, "2099-01-01").read_text(encoding="utf-8")
    assert "burn_kcal: 150" in output
    assert "net_kcal: -50" in output


def test_usda_search_mapping_without_network(monkeypatch):
    monkeypatch.setattr(
        health_usda,
        "_http_get_json",
        lambda _url: {
            "foods": [{
                "fdcId": 1,
                "description": "Synthetic food",
                "dataType": "Foundation",
                "foodNutrients": [
                    {"nutrientId": 1008, "value": 100},
                    {"nutrientId": 1005, "value": 25},
                ],
            }]
        },
    )
    result = health_usda.search_usda("synthetic", "placeholder-key")
    assert result[0]["per_100g"]["calories"] == 100
    assert result[0]["per_100g"]["carbs_g"] == 25


def test_burn_estimator_uses_only_synthetic_history(tmp_path):
    ledger = tmp_path / "burn-ledger.md"
    rows = [
        "| date | burn_kcal | steps | active_min | partial | suspect |",
        "|---|---:|---:|---:|---|---|",
    ]
    for index in range(35):
        day = date(2099, 1, 1) + timedelta(days=index)
        rows.append(
            f"| {day.isoformat()} | {1600 + index * 10} | "
            f"{3000 + index * 100} | {20 + index} | no | no |"
        )
    ledger.write_text("\n".join(rows), encoding="utf-8")
    result = estimate_burn(ledger, 5000)
    assert result["estimated"] is True
    assert result["n_days"] == 35
