"""실제 원고·계획서 쌍의 결과가 골든과 같은가. 픽스처 파일이 없으면 건너뛴다.

골든 갱신(판정 정책을 의도적으로 바꿨을 때만): python tools/make_golden.py tests/fixtures/<원고> tests/fixtures/<계획서>
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from make_golden import golden_of  # noqa: E402

from ncs_review import run_all  # noqa: E402

PAIRS = [
    ("LM1203020201_24v3", "LM1203020201_24v3_light.hwpx", "개발계획서_12030202.hwp"),
]


@pytest.mark.parametrize("code,manuscript,plan", PAIRS)
def test_real_pair_matches_golden(code, manuscript, plan):
    fixtures = ROOT / "tests" / "fixtures"
    golden_path = ROOT / "tests" / "golden" / f"{code}.json"
    if not (fixtures / manuscript).exists() or not (fixtures / plan).exists():
        pytest.skip(f"픽스처 없음: tests/fixtures/{manuscript}, {plan}")
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    actual = json.loads(json.dumps(golden_of(run_all([str(fixtures / manuscript), str(fixtures / plan)])), ensure_ascii=False))
    assert actual["summary"] == golden["summary"]
    for key, area in golden["areas"].items():
        assert actual["areas"][key]["status"] == area["status"], key
        assert actual["areas"][key].get("checklist") == area.get("checklist"), f"{key} 체크리스트가 골든과 다름"
        assert actual["areas"][key].get("diagnostics") == area.get("diagnostics"), f"{key} 진단이 골든과 다름"
