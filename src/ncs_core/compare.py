"""목록 비교: difflib로 누락/추가/변경/순서를 구분한다. 차례·개요·필요지식 규칙이 함께 쓴다.

중간에 하나가 빠져도 뒤가 연쇄로 '다름'이 되지 않는다.
비고 문구의 두 쪽 이름(actual_label/expected_label)은 호출하는 영역이 정한다.
"""

import difflib
from collections.abc import Callable, Sequence

from .text import O, X, visible


def diff_list(
    label: str,
    expected: Sequence[str],
    actual: Sequence[str],
    *,
    norm: Callable[[str | None], str],
    actual_label: str,
    expected_label: str,
) -> tuple[str, list[str]]:
    """→ (체크값 O/X, 비고 목록)."""
    exp, act = [norm(x) for x in expected], [norm(x) for x in actual]
    notes: list[str] = []
    if len(expected) != len(actual):
        notes.append(f"{label} 개수: {actual_label} {len(actual)} / {expected_label} {len(expected)}")
    if exp != act and sorted(exp) == sorted(act):
        notes.append(f"{label} 순서 다름: {actual_label} {[visible(x) for x in actual]} / {expected_label} {list(expected)}")
        return X, notes
    matcher = difflib.SequenceMatcher(None, exp, act, autojunk=False)
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            continue
        if op == "replace" and i2 - i1 == j2 - j1:
            for k in range(i2 - i1):
                notes.append(f'{label} {i1 + k + 1}번째 다름: "{visible(actual[j1 + k])}" / {expected_label} "{expected[i1 + k]}"')
        else:
            for k in range(i1, i2):
                notes.append(f'{label} {k + 1}번째 누락: "{expected[k]}"')
            for k in range(j1, j2):
                notes.append(f'{label} {actual_label} {k + 1}번째가 {expected_label}에 없음: "{visible(actual[k])}"')
    return (O if not notes else X), notes
