"""검수 전체의 설정 한 곳. 영역별 CheckConfig 는 여기서 만든다.

기본값은 각 패키지 CheckConfig 의 기본값과 같다(판정 불변). 값을 바꾸면 모든 영역에 함께 적용된다.
"""

from dataclasses import dataclass, field

import ncs_knowledge.config
import ncs_overview.config
import ncs_position.config
import ncs_toc.config


@dataclass(frozen=True)
class ReviewConfig:
    # 양식: 섹션 배치
    front_section: int = 0   # 차례·개요·위치가 있는 섹션
    body_section: int = 1    # 본문 섹션
    areas: tuple[str, ...] = field(default=("toc", "overview", "knowledge", "position"))  # 실행할 영역 key

    # 차례·본문 파서 휴리스틱 (ncs_toc.CheckConfig)
    body_heading_max_length: int = 60
    eval_candidate_max_length: int = 30
    tail_min_paragraphs: int = 3
    reference_min_lines: int = 3
    ambiguous_tail_min_paragraphs: int = 10

    # 개요 (ncs_overview.CheckConfig)
    max_prerequisites: int = 5       # ② 선수학습 최대 개수
    max_terms: int = 10              # ⑧ 핵심 용어 최대 개수
    term_max_length: int = 25        # ⑧ 이보다 긴 항목은 단어가 아닐 가능성 → △

    # 필요지식 (ncs_knowledge.CheckConfig)
    goal_lookahead: int = 8          # ⑤ N-M. 제목 뒤 몇 줄 안에서 '학습 목표' 줄을 찾는가
    goal_similarity: float = 0.8     # ⑤ 이 이상이면 윤문 수준 차이(△), 미만이면 불일치(X)
    whitespace_is_difference: bool = True  # ⑤ 공백·문장부호만 다른 학습 목표를 X로 볼지
    figtab_min_agreement: float = 0.5  # ⑦ 캡션 앞 번호와 학습 경계 일치율이 이 미만이면 '-위치' 검사 생략
    source_lookback: int = 3         # ⑧ 그림 캡션 위 몇 줄 안에서 출처 줄을 찾는가
    source_lookahead: int = 80       # ⑧ 표 캡션 아래 몇 줄 안에서 출처 줄을 찾는가

    def __post_init__(self):
        if self.front_section < 0 or self.body_section < 0:
            raise ValueError("섹션 번호는 0 이상이어야 합니다")
        if self.front_section == self.body_section:
            raise ValueError("차례·개요와 본문이 별도 섹션인 양식만 지원합니다")
        if not self.areas:
            raise ValueError("실행할 영역이 하나 이상 있어야 합니다")
        # 값 범위 검증은 각 패키지 CheckConfig 가 한다.
        self.toc_config(), self.overview_config(), self.knowledge_config(), self.position_config()

    def toc_config(self) -> ncs_toc.config.CheckConfig:
        return ncs_toc.config.CheckConfig(
            front_section=self.front_section,
            body_section=self.body_section,
            body_heading_max_length=self.body_heading_max_length,
            eval_candidate_max_length=self.eval_candidate_max_length,
            tail_min_paragraphs=self.tail_min_paragraphs,
            reference_min_lines=self.reference_min_lines,
            ambiguous_tail_min_paragraphs=self.ambiguous_tail_min_paragraphs,
        )

    def overview_config(self) -> ncs_overview.config.CheckConfig:
        return ncs_overview.config.CheckConfig(
            front_section=self.front_section,
            max_prerequisites=self.max_prerequisites,
            max_terms=self.max_terms,
            term_max_length=self.term_max_length,
        )

    def knowledge_config(self) -> ncs_knowledge.config.CheckConfig:
        return ncs_knowledge.config.CheckConfig(
            front_section=self.front_section,
            body_section=self.body_section,
            goal_lookahead=self.goal_lookahead,
            goal_similarity=self.goal_similarity,
            whitespace_is_difference=self.whitespace_is_difference,
            figtab_min_agreement=self.figtab_min_agreement,
            source_lookback=self.source_lookback,
            source_lookahead=self.source_lookahead,
        )

    def position_config(self) -> ncs_position.config.CheckConfig:
        return ncs_position.config.CheckConfig(front_section=self.front_section)


DEFAULT_CONFIG = ReviewConfig()
