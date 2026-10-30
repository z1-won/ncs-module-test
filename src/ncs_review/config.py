"""실행 전체에 공통인 양식 가정. 영역별 세부 임계값은 각 패키지의 CheckConfig 기본값을 쓴다.

2단계(통합 파이프라인)에서 영역별 임계값도 이 한 곳으로 모은다.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReviewConfig:
    front_section: int = 0   # 차례·개요·위치가 있는 섹션
    body_section: int = 1    # 본문 섹션
    areas: tuple[str, ...] = field(default=("toc", "overview", "knowledge", "position"))  # 실행할 영역 key

    def __post_init__(self):
        if self.front_section < 0 or self.body_section < 0:
            raise ValueError("섹션 번호는 0 이상이어야 합니다")
        if self.front_section == self.body_section:
            raise ValueError("차례·개요와 본문이 별도 섹션인 양식만 지원합니다")
        if not self.areas:
            raise ValueError("실행할 영역이 하나 이상 있어야 합니다")


DEFAULT_CONFIG = ReviewConfig()
