"""규칙 실행과 진단. 추출(ReviewContext 조립)은 ncs_review.extract / ncs_review.areas 가 한다."""

from collections.abc import Sequence

from ncs_core import ReviewResult, Rule, run_rules
from ncs_core.sections import relabel_sections
from ncs_core.text import flatten

from .models import ReviewContext
from .registry import ALL_ITEM_IDS, DEFAULT_RULES


def _diagnostics(context: ReviewContext, rules: Sequence[Rule]) -> dict:
    manuscript, plan, config = context.manuscript, context.plan, context.config
    warnings = []
    if not context.plan_toc:
        warnings.append("개발계획서가 없거나 해당 모듈 블록을 읽지 못했습니다")
    elif not context.plan_toc["학습명"] or not context.plan_toc["내용명"]:
        warnings.append("개발계획서 명칭을 일부만 읽었습니다. 항목별 비교 기준을 확인하세요")
    if not context.body["lessons"]:
        warnings.append("본문 학습 구간을 읽지 못했습니다. 평가 대조와 ④ 교수·학습 방법/평가 위치는 판단불가입니다")
    if not context.eval_tables:
        warnings.append("평가 표 셀 정보가 없어 문단 휴리스틱으로 비교합니다")
    if len(manuscript.sections) > 2:
        warnings.append("선택한 차례/개요 및 본문 섹션만 검사합니다. 다른 섹션에 이어진 본문은 검사하지 않습니다")
    implemented = {rule.item_prefix for rule in rules}
    return {
        "module_code": context.module_code,
        "inputs": {"manuscript": str(manuscript.path), "plan": str(plan.path) if plan else None},
        "format": manuscript.format,
        "sections": {"front": config.front_section, "body": config.body_section},
        "counts": {
            "lessons": len(context.toc["학습"]),
            "contents": len(context.toc["내용"]),
            "navigator_runs": len(context.body["nav_runs"]),
            "evaluation_tables": len(context.eval_tables),
        },
        "implemented": sorted(implemented),
        "not_implemented": [item for item in ALL_ITEM_IDS if item not in implemented],
        "warnings": warnings,
    }


def evaluate_review(context: ReviewContext, *, rules: Sequence[Rule] = DEFAULT_RULES) -> ReviewResult:
    """한 실행의 결과만 돌려준다. 같은 context를 다시 실행해도 이전 결과를 누적하지 않는다."""
    config = context.config
    mapping = {0: config.front_section, 1: config.body_section}
    checklist = run_rules(context, rules)
    for row in checklist:
        row["region_path"] = relabel_sections(row["region_path"], mapping)
        row["비고"] = relabel_sections(row["비고"], mapping)
        if row["item_id"] == "F02-차례-⑤":
            row["원고"] = relabel_sections(row["원고"], mapping)
    diagnostics = _diagnostics(context, rules)
    return ReviewResult(context.module_code, checklist, flatten(checklist), diagnostics, context)
