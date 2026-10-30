"""문서 1회 읽기 → 영역별 독립 실행(부분 실패 허용) → 종합 요약."""

from __future__ import annotations

import traceback
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ncs_core import Document, ReviewResult, resolve_module_code, select_documents
from ncs_core.reporting import overall_verdict
from ncs_core.text import UNDECIDED, VERDICTS

from . import __version__ as ENGINE_VERSION
from .areas import AREAS, Area, run_area
from .config import DEFAULT_CONFIG, ReviewConfig

OK, FAILED, SKIPPED = "ok", "failed", "skipped"


@dataclass
class AreaOutcome:
    area: Area
    status: str                          # ok / failed / skipped
    result: ReviewResult | None = None
    error: str | None = None             # 사용자에게 보여줄 한 줄
    traceback: str | None = None         # 예기치 못한 예외일 때만

    @property
    def verdict(self) -> str | None:
        if self.result is None:
            return None
        return overall_verdict(row["판정"] for row in self.result.checklist)


@dataclass
class RunResult:
    module_code: str
    manuscript: Document
    plan: Document | None
    config: ReviewConfig
    outcomes: dict[str, AreaOutcome] = field(default_factory=dict)

    @property
    def verdict(self) -> str:
        """영역 종합: 부적합 > 판단불가 > 적합. 실패한 영역이 있으면 적합이라 하지 않는다."""
        verdicts = [o.verdict for o in self.outcomes.values() if o.verdict]
        value = overall_verdict(verdicts)
        if any(o.status == FAILED for o in self.outcomes.values()) and value != "부적합":
            return UNDECIDED
        return value

    @property
    def findings(self) -> list[dict]:
        return [f for o in self.outcomes.values() if o.result for f in o.result.findings]

    def summary(self) -> dict[str, Any]:
        areas: dict[str, Any] = {}
        for key, outcome in self.outcomes.items():
            entry: dict[str, Any] = {"이름": outcome.area.name, "상태": outcome.status}
            if outcome.result is not None:
                verdicts = [row["판정"] for row in outcome.result.checklist]
                entry["검수결과"] = outcome.verdict
                entry["행 수"] = {v: verdicts.count(v) for v in VERDICTS}
                entry["지적사항"] = len(outcome.result.findings)
                entry["warnings"] = outcome.result.diagnostics.get("warnings", [])
                entry["not_implemented"] = outcome.result.diagnostics.get("not_implemented", [])
            if outcome.error:
                entry["오류"] = outcome.error
            areas[key] = entry
        return {
            "module_code": self.module_code,
            "engine_version": ENGINE_VERSION,
            "inputs": {"manuscript": str(self.manuscript.path), "plan": str(self.plan.path) if self.plan else None},
            "format": self.manuscript.format,
            "sections": {"front": self.config.front_section, "body": self.config.body_section},
            "검수결과": self.verdict,
            "failed": [k for k, o in self.outcomes.items() if o.status == FAILED],
            "skipped": [k for k, o in self.outcomes.items() if o.status == SKIPPED],
            "영역": areas,
        }


def run_documents(
    manuscript: Document,
    plan: Document | None,
    *,
    module_code: str = "",
    config: ReviewConfig = DEFAULT_CONFIG,
    areas: Mapping[str, Area] = AREAS,
) -> RunResult:
    """이미 읽은 Document 로 실행한다(서비스 워커가 파일 저장소에서 읽어 넘길 때)."""
    code = resolve_module_code(manuscript.path, module_code)
    run = RunResult(code, manuscript, plan, config)
    for key in config.areas:
        area = areas.get(key)
        if area is None:
            raise ValueError(f"알 수 없는 검수 영역: {key} (가능: {', '.join(areas)})")
        if area.requires_plan and plan is None:
            run.outcomes[key] = AreaOutcome(area, SKIPPED, error="개발계획서가 없어 이 영역은 실행하지 않음")
            continue
        try:
            run.outcomes[key] = AreaOutcome(area, OK, result=run_area(area, manuscript, plan, code, config))
        except ValueError as error:  # 양식·섹션·입력 문제: 메시지가 곧 사용자 안내
            run.outcomes[key] = AreaOutcome(area, FAILED, error=str(error))
        except Exception as error:  # noqa: BLE001 — 한 영역의 버그가 다른 영역 결과를 막지 않게 한다
            run.outcomes[key] = AreaOutcome(
                area, FAILED, error=f"내부 오류({type(error).__name__}): {error}", traceback=traceback.format_exc()
            )
    return run


def run_all(
    paths,
    *,
    roles: dict | None = None,
    module_code: str = "",
    config: ReviewConfig = DEFAULT_CONFIG,
    areas: Mapping[str, Area] = AREAS,
) -> RunResult:
    """paths: 원고 1개 + 선택적 개발계획서 1개. 역할은 내용으로 판별하고 roles 로 덮어쓴다."""
    documents = select_documents(paths, roles, required=("manuscript",))
    return run_documents(documents["manuscript"], documents.get("plan"), module_code=module_code, config=config, areas=areas)
