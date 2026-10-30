"""차례 검수의 목록 비교. 정책은 ncs_core.compare.diff_list, 문구는 '이 자리 / 기준'."""

from collections.abc import Iterable, Sequence

from ncs_core import O, PUA, X, visible
from ncs_core.compare import diff_list as _diff_list

from .text import norm


def diff_list(label: str, expected: Sequence[str], actual: Sequence[str]) -> tuple[str, list[str]]:
    return _diff_list(label, expected, actual, norm=norm, actual_label="이 자리", expected_label="기준")


def pua_note(texts: Iterable[str], already: Iterable[str] = ()) -> tuple[str, list[str]]:
    """already: 차례(①)에서 이미 보고된 문자열(PUA→· 치환형). 같은 원인이면 X 대신 비고만."""
    already = set(already)
    bad = [t for t in texts if PUA.search(t)]
    new = [t for t in bad if PUA.sub("·", t) not in already]
    notes = [f"기호 글꼴 문자: {visible(t)}" for t in new]
    if bad and not new:
        notes.append("기호 글꼴 문자가 있으나 차례와 같은 원인 (①에서 보고됨)")
    return (X if new else O), notes
