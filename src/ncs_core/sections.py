"""결과의 논리적 섹션 표기(section0=차례·개요, section1=본문)를 실제 입력 섹션 번호로 바꾼다."""

import re
from typing import Any


def relabel_sections(value: Any, mapping: dict[int, int]) -> Any:
    """문자열·dict·list 안의 'section<n>' 을 mapping 대로 바꾼다. 그 밖의 값은 그대로."""
    if isinstance(value, str):
        return re.sub(r"section(\d+)\b", lambda m: "section" + str(mapping.get(int(m[1]), int(m[1]))), value)
    if isinstance(value, dict):
        return {k: relabel_sections(v, mapping) for k, v in value.items()}
    if isinstance(value, list):
        return [relabel_sections(v, mapping) for v in value]
    return value
