from ncs_core import FAIL, NA, O, PASS, TRI, UNDECIDED, X, flatten, make_normalizer, verdict, visible
from ncs_overview.text import split_items


def test_verdict_priority():
    assert verdict({"a": O}) == PASS
    assert verdict({"a": O, "b": TRI}) == UNDECIDED
    assert verdict({"a": TRI, "b": X}) == FAIL
    assert verdict({"a": NA}) == PASS  # '-' 는 무시


def test_normalizer_strips_head_number_and_pua():
    norm, same = make_normalizer(r"^\d+(-\d+)?\.\s*")
    assert norm("1-1. 예약  접수") == "예약 접수"
    assert same("객실부대시설", "객실·부대시설")
    assert not same("예약현황", "예약 현황")  # 공백 차이는 다른 글자
    assert visible("객실부대") == "객실⟨U+F0B7⟩부대"


def test_flatten_keeps_only_x_and_triangle():
    rows = [{
        "item_id": "F02-차례-①", "region_path": "section0 > 차례", "원고": "x",
        "체크": {"a": O, "b": X, "c": TRI}, "판정": FAIL, "비고": {"b": "이유"}, "수정 제안": None,
    }]
    findings = flatten(rows)
    assert [(f["check"], f["verdict"]) for f in findings] == [("b", FAIL), ("c", UNDECIDED)]
    assert findings[0]["reason"] == "이유"


def test_split_items_respects_brackets():
    assert split_items("예약, 체크 인(Check In, 투숙), 객실") == ["예약", "체크 인(Check In, 투숙)", "객실"]
