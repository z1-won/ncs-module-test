"""한 실행의 결과를 폴더 하나에 모은다.

<out_dir>/<코드>_<실행별 폴더>/
    <코드>_<영역 항목 꼬리말>.json      영역별 체크리스트 (기존 save_results 와 같은 이름)
    <코드>_<영역>_00_요약.json 등        영역별 요약·지적사항·전체·진단 (기존과 같음)
    <코드>_00_종합요약.json               영역 종합 검수결과 + 실패·생략 영역
    <코드>_지적사항.json                  모든 영역의 X·△ 행
    <코드>_검수결과.zip                   위 JSON 전부
"""

from __future__ import annotations

import json
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from ncs_core import validate_module_code

from .orchestrator import OK, RunResult


@dataclass(frozen=True)
class SavedRun:
    directory: Path
    zip_path: Path
    summary: dict


def save_run(run: RunResult, out_dir="결과", *, per_run_dir: bool = True) -> SavedRun:
    code = validate_module_code(run.module_code)
    root = Path(out_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix=f"{code}_", dir=root)) if per_run_dir else root

    for outcome in run.outcomes.values():
        if outcome.status == OK and outcome.result is not None:
            outcome.area.save(outcome.result, directory, per_run_dir=False)

    def write(tail: str, value) -> Path:
        path = directory / f"{code}_{tail}.json"
        path.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding="utf-8")
        return path

    summary = run.summary()
    write("00_종합요약", summary)
    write("지적사항", run.findings)
    failures = {k: o.traceback for k, o in run.outcomes.items() if o.traceback}
    if failures:
        write("오류", failures)

    zip_path = directory / f"{code}_검수결과.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.glob("*.json")):
            archive.write(path, path.name)
    return SavedRun(directory, zip_path, summary)
