"""검수 영역 정의. 영역 하나 = 기존 패키지 하나(prepare → evaluate → save).

새 영역(예: 이미지 해상도, 수행 내용)을 붙이려면 같은 계약으로 Area 를 하나 더 등록하면 된다.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import ncs_knowledge
import ncs_overview
import ncs_position
import ncs_toc
from ncs_core import Document, ReviewResult, SavedReport

from .config import ReviewConfig


@dataclass(frozen=True)
class Area:
    key: str                     # CLI·설정에서 쓰는 영어 키
    name: str                    # 결과 파일 이름에 쓰는 한국어 이름(기존 save_results 와 같음)
    item_prefix: str             # 이 영역 행의 item_id 접두
    requires_plan: bool          # 개발계획서가 없으면 skipped
    make_config: Callable[[ReviewConfig], Any]
    prepare: Callable[..., Any]  # prepare(manuscript, plan, *, module_code, config) -> context
    evaluate: Callable[[Any], ReviewResult]
    save: Callable[..., SavedReport]  # save(result, out_dir, *, per_run_dir)


AREAS: dict[str, Area] = {
    area.key: area
    for area in (
        Area(
            "toc", "차례", "F02-차례-", False,
            lambda c: ncs_toc.CheckConfig(front_section=c.front_section, body_section=c.body_section),
            ncs_toc.prepare_review, ncs_toc.evaluate_review, ncs_toc.save_results,
        ),
        Area(
            "overview", "개요", "F02-개요-", False,
            lambda c: ncs_overview.CheckConfig(front_section=c.front_section),
            ncs_overview.prepare_review, ncs_overview.evaluate_review, ncs_overview.save_results,
        ),
        Area(
            "knowledge", "필요지식", "F02-필요지식-", False,
            lambda c: ncs_knowledge.CheckConfig(front_section=c.front_section, body_section=c.body_section),
            ncs_knowledge.prepare_review, ncs_knowledge.evaluate_review, ncs_knowledge.save_results,
        ),
        Area(
            "position", "위치", "F02-위치-", True,
            lambda c: ncs_position.CheckConfig(front_section=c.front_section),
            ncs_position.prepare_review, ncs_position.evaluate_review, ncs_position.save_results,
        ),
    )
}


def run_area(area: Area, manuscript: Document, plan: Document | None, module_code: str, config: ReviewConfig) -> ReviewResult:
    context = area.prepare(manuscript, plan, module_code=module_code, config=area.make_config(config))
    return area.evaluate(context)
