"""검수 영역 정의. 영역 하나 = 기존 패키지 하나(컨텍스트 어댑터 → evaluate → save).

추출은 ExtractedDocuments 가 한 번만 하고, 각 영역의 어댑터는 그 추출물로 해당 패키지의
ReviewContext 를 조립해 기존 evaluate_review 를 그대로 호출한다. 규칙 코드는 건드리지 않는다.
새 영역(예: 이미지 해상도, 수행 내용)을 붙이려면 같은 계약으로 Area 를 하나 더 등록하면 된다.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import ncs_knowledge
import ncs_knowledge.models
import ncs_overview
import ncs_overview.models
import ncs_position
import ncs_position.models
import ncs_toc
import ncs_toc.models
from ncs_core import ReviewResult, SavedReport

from .extract import ExtractedDocuments


@dataclass(frozen=True)
class Area:
    key: str                     # CLI·설정에서 쓰는 영어 키
    name: str                    # 결과 파일 이름에 쓰는 한국어 이름(기존 save_results 와 같음)
    item_prefix: str             # 이 영역 행의 item_id 접두
    requires_plan: bool          # 개발계획서가 없으면 skipped
    build: Callable[[ExtractedDocuments], Any]  # 추출물 → 패키지 ReviewContext
    evaluate: Callable[[Any], ReviewResult]
    save: Callable[..., SavedReport]  # save(result, out_dir, *, per_run_dir)


def _toc_context(x: ExtractedDocuments) -> ncs_toc.models.ReviewContext:
    return ncs_toc.models.ReviewContext(
        x.manuscript, x.plan, x.module_code, x.config.toc_config(),
        x.toc, x.toc_overview, x.plan_toc, x.body, x.presence, x.eval_tables,
    )


def _overview_context(x: ExtractedDocuments) -> ncs_overview.models.ReviewContext:
    return ncs_overview.models.ReviewContext(
        x.manuscript, x.plan, x.module_code, x.config.overview_config(), x.overview, x.plan_info,
    )


def _knowledge_context(x: ExtractedDocuments) -> ncs_knowledge.models.ReviewContext:
    return ncs_knowledge.models.ReviewContext(
        x.manuscript, x.plan, x.module_code, x.config.knowledge_config(),
        x.toc, x.structure, x.body, x.units, x.plan_goals, x.table_paragraphs, x.labels,
    )


def _position_context(x: ExtractedDocuments) -> ncs_position.models.ReviewContext:
    if x.plan is None:
        raise ValueError("위치 검수에는 개발계획서가 필요합니다")
    x.front_lines  # 섹션 검증 (없으면 ValueError)
    return ncs_position.models.ReviewContext(
        x.manuscript, x.plan, x.module_code, x.config.position_config(),
        x.plan_classification, x.manuscript_classification, x.plan_position, x.manuscript_position,
        x.styled_table, x.plan_module_name,
    )


AREAS: dict[str, Area] = {
    area.key: area
    for area in (
        Area("toc", "차례", "F02-차례-", False, _toc_context, ncs_toc.evaluate_review, ncs_toc.save_results),
        Area("overview", "개요", "F02-개요-", False, _overview_context, ncs_overview.evaluate_review, ncs_overview.save_results),
        Area("knowledge", "필요지식", "F02-필요지식-", False, _knowledge_context, ncs_knowledge.evaluate_review, ncs_knowledge.save_results),
        Area("position", "위치", "F02-위치-", True, _position_context, ncs_position.evaluate_review, ncs_position.save_results),
    )
}


def run_area(area: Area, extracted: ExtractedDocuments) -> ReviewResult:
    return area.evaluate(area.build(extracted))
