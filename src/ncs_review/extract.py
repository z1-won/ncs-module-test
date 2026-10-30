"""원고·개발계획서에서 네 영역이 쓰는 모든 추출물을 한 번만 만든다.

각 추출물은 지연 계산·캐시 속성이다. 어떤 영역이 먼저 요청하든 같은 객체를 돌려주고,
한 추출물이 실패해도 그것을 쓰지 않는 영역은 영향을 받지 않는다.
파서는 기존 패키지의 것을 그대로 호출한다(판정 불변).
"""

from __future__ import annotations

from functools import cached_property
from typing import Any

from ncs_core import Document, Table
from ncs_knowledge.figtab import _flatten, collect_labels
from ncs_knowledge.plan import parse_plan_goals
from ncs_knowledge.structure import unit_regions
from ncs_overview.parsers import parse_overview as parse_overview_full
from ncs_overview.parsers import parse_plan as parse_plan_block
from ncs_position.parsers import find_styled_position_table, parse_classification, parse_plan_module_name, parse_position
from ncs_toc.evaluation import evaluation_tables
from ncs_toc.parsers import parse_body, parse_overview as parse_overview_structure, parse_plan_toc, parse_toc
from ncs_toc.presence import section_presence

from .config import ReviewConfig

NO_FRONT = "지정한 개요 섹션이 없습니다. 문서 구조와 CheckConfig를 확인하세요"
NO_BODY = "지정한 차례/본문 섹션이 없습니다. 문서 구조와 CheckConfig를 확인하세요"
NO_TOC = "차례 또는 차례 학습명을 읽지 못했습니다. 양식과 섹션 설정을 확인하세요"
NO_OVERVIEW = "학습모듈의 개요를 읽지 못했습니다. 양식과 섹션 설정을 확인하세요"


class ExtractedDocuments:
    """원고(+계획서) 한 쌍의 추출물. 속성 이름은 각 패키지 ReviewContext 의 필드 이름을 따른다."""

    def __init__(self, manuscript: Document, plan: Document | None, module_code: str, config: ReviewConfig):
        self.manuscript = manuscript
        self.plan = plan
        self.module_code = module_code
        self.config = config

    # ---------------------------------------------------------------- 섹션

    @cached_property
    def front_lines(self) -> list[str]:
        if self.config.front_section >= len(self.manuscript.sections):
            raise ValueError(NO_FRONT)
        return [l for l in self.manuscript.sections[self.config.front_section] if l]

    @cached_property
    def sections(self) -> list[list[str]]:
        """파서의 논리적 [section0=차례·개요, section1=본문]."""
        if max(self.config.front_section, self.config.body_section) >= len(self.manuscript.sections):
            raise ValueError(NO_BODY)
        return [self.manuscript.sections[self.config.front_section], self.manuscript.sections[self.config.body_section]]

    @cached_property
    def body_images(self) -> list[tuple[int, str]]:
        return [(p, name) for s, p, name in self.manuscript.images if s == self.config.body_section]

    # ---------------------------------------------------------------- 차례·본문 (ncs_toc)

    @cached_property
    def toc(self) -> dict[str, Any]:
        toc = parse_toc(self.sections)
        if not toc or not toc["학습"]:
            raise ValueError(NO_TOC)
        return toc

    @cached_property
    def toc_overview(self) -> dict[str, Any] | None:
        """차례 검수용 내용체계 (학습·내용 줄만). ncs_toc.parsers.parse_overview."""
        return parse_overview_structure(self.sections)

    @cached_property
    def plan_toc(self) -> dict[str, Any] | None:
        return parse_plan_toc(self.plan.sections, self.module_code) if self.plan else None

    @cached_property
    def presence(self) -> dict[str, Any]:
        return section_presence(self.sections, self.body_images, self.config.toc_config())

    @cached_property
    def body(self) -> dict[str, Any]:
        return parse_body(self.sections, len(self.toc["학습"]), cutoff=self.presence["참고 자료"]["k"], config=self.config.toc_config())

    @cached_property
    def eval_tables(self) -> list[tuple[int, str, list[str]]]:
        return evaluation_tables(self.manuscript.section_tables(self.config.body_section))

    # ---------------------------------------------------------------- 개요 (ncs_overview)

    @cached_property
    def _overview_raw(self) -> dict[str, Any]:
        if self.config.front_section >= len(self.manuscript.sections):
            raise ValueError(NO_FRONT)
        return parse_overview_full(self.manuscript, self.config.front_section)

    @cached_property
    def overview(self) -> dict[str, Any]:
        """학습모듈의 개요 전체(목표·선수학습·내용체계·핵심 용어). ncs_overview.parsers.parse_overview."""
        overview = self._overview_raw
        if overview["개요 제목 p"] is None and not any(overview.get(k) for k in ("목표", "선수학습", "내용체계", "핵심 용어")):
            raise ValueError(NO_OVERVIEW)
        return overview

    @cached_property
    def plan_info(self) -> dict[str, Any] | None:
        return parse_plan_block(self.plan, self.module_code) if self.plan else None

    # ---------------------------------------------------------------- 필요지식 (ncs_knowledge)

    @cached_property
    def structure(self) -> dict[str, Any] | None:
        """내용체계 표 (개요 추출의 '내용체계'). 개요 블록 전체를 못 읽어도 필요지식은 돌아간다(기존 동작)."""
        return self._overview_raw.get("내용체계")

    @cached_property
    def units(self) -> list[dict[str, Any]]:
        return unit_regions(self.body, self.config.knowledge_config())

    @cached_property
    def plan_goals(self) -> dict[str, Any] | None:
        return parse_plan_goals(self.plan, self.module_code) if self.plan else None

    @cached_property
    def table_paragraphs(self) -> set[int] | None:
        return self.manuscript.section_table_paragraphs(self.config.body_section)

    @cached_property
    def labels(self) -> dict[str, Any]:
        flat = _flatten(self.sections)
        caps, refs, bare = collect_labels(flat)
        body = self.body
        position = {(s, i): k for k, (s, i, _) in enumerate(flat)}
        lesson_spans = [
            (no, position[(1, body["lines"][a][0])], position[(1, body["lines"][b][0])] if b < len(body["lines"]) else len(flat))
            for no, a, b in body["spans"]
        ]
        return {"flat": flat, "caps": caps, "refs": refs, "bare": bare, "lesson_spans": lesson_spans}

    # ---------------------------------------------------------------- 위치 (ncs_position)

    @cached_property
    def plan_lines(self) -> list[str]:
        return [l for section in self.plan.sections for l in section] if self.plan else []

    @cached_property
    def plan_classification(self) -> dict[str, str]:
        return parse_classification(self.plan_lines)

    @cached_property
    def manuscript_classification(self) -> dict[str, str]:
        return parse_classification(self.front_lines)

    @cached_property
    def plan_position(self) -> dict[str, Any]:
        return parse_position(self.plan.tables if self.plan else [])

    @cached_property
    def manuscript_position(self) -> dict[str, Any]:
        return parse_position(self.manuscript.tables)

    @cached_property
    def styled_table(self) -> Table | None:
        return find_styled_position_table(self.manuscript.tables) if self.manuscript.has_styles else None

    @cached_property
    def plan_module_name(self) -> str | None:
        return parse_plan_module_name(self.plan.sections, self.module_code) if self.plan else None
