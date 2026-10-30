"""개요 검수의 목록 비교. 정책은 ncs_core.compare.diff_list, 문구는 '원고 / 개발계획서'."""

from collections.abc import Sequence

from ncs_core.compare import diff_list as _diff_list

from .text import norm


def diff_list(label: str, expected: Sequence[str], actual: Sequence[str]) -> tuple[str, list[str]]:
    return _diff_list(label, expected, actual, norm=norm, actual_label="원고", expected_label="개발계획서")
