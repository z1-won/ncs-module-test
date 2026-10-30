"""실제 원고·계획서 쌍의 검수 결과를 골든 JSON으로 저장한다 (판정 불변 회귀 기준).

사용: python tools/make_golden.py 원고.hwpx 개발계획서.hwp [--out tests/golden/<코드>.json]
저장 내용: 종합 요약 + 영역별 체크리스트·진단 (입력 경로는 파일 이름만 남겨 환경 독립).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ncs_review import run_all


def normalize(value):
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v) for v in value]
    return value


def golden_of(run) -> dict:
    summary = run.summary()
    summary["inputs"] = {k: (Path(v).name if v else None) for k, v in summary["inputs"].items()}
    areas = {}
    for key, outcome in run.outcomes.items():
        entry = {"status": outcome.status, "error": outcome.error}
        if outcome.result is not None:
            diagnostics = dict(outcome.result.diagnostics)
            diagnostics["inputs"] = {k: (Path(v).name if v else None) for k, v in diagnostics.get("inputs", {}).items()}
            entry["checklist"] = normalize(outcome.result.checklist)
            entry["diagnostics"] = diagnostics
        areas[key] = entry
    return {"summary": summary, "areas": areas}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--out")
    args = parser.parse_args()
    run = run_all(args.paths)
    out = Path(args.out) if args.out else Path("tests/golden") / f"{run.module_code}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(golden_of(run), ensure_ascii=False, indent=1), encoding="utf-8")
    rows = sum(len(a.get("checklist", [])) for a in golden_of(run)["areas"].values())
    print(f"{out} ← {run.module_code}: 종합 {run.verdict}, 행 {rows}개, 지적 {len(run.findings)}건")


if __name__ == "__main__":
    main()
