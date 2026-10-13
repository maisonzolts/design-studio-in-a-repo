from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import indesign_preflight


def test_bridge_defaults_to_loopback(monkeypatch):
    monkeypatch.delenv("INDESIGN_BRIDGE_URL", raising=False)
    import importlib
    import idbridge
    importlib.reload(idbridge)
    assert idbridge.BRIDGE == "http://127.0.0.1:3000"


def test_comp_measure_uses_a_file_url():
    text = (ROOT / "scripts" / "comp_measure.py").read_text(encoding="utf-8")
    assert "file:///" in text
    assert ("<" + "DRIVE_ROOT>") not in text


def test_empty_document_is_unverifiable():
    report = indesign_preflight.judge({"frames": []})
    assert report["verdict"] == "unverifiable"


def test_structured_document_passes():
    facts = {
        "frames": [{"page": 1, "words": 4, "style": "Body", "gb": [0, 0, 1, 1]}],
        "paragraph_styles": ["Body"],
        "swatches": [],
        "layers": ["Artwork"],
        "pw": 8.5,
        "ph": 11,
    }
    assert indesign_preflight.judge(facts)["verdict"] == "pass"
