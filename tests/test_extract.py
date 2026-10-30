"""ExtractedDocuments: 파서는 한 번만, 추출 실패는 그 추출물을 쓰는 영역에만."""

from pathlib import Path

from hwpx_builder import manuscript_sections, write_hwpx

import ncs_review.extract as extract
from ncs_core import load_document
from ncs_review import ReviewConfig, run_all, run_documents
from ncs_review.orchestrator import FAILED, OK


def test_parsers_run_once_for_all_areas(sample_pair, monkeypatch):
    calls = {"toc": 0, "body": 0, "overview": 0, "plan": 0}
    originals = {k: getattr(extract, name) for k, name in
                 (("toc", "parse_toc"), ("body", "parse_body"), ("overview", "parse_overview_full"), ("plan", "parse_plan_block"))}

    def counting(key, name):
        def wrapper(*args, **kwargs):
            calls[key] += 1
            return originals[key](*args, **kwargs)
        monkeypatch.setattr(extract, name, wrapper)

    counting("toc", "parse_toc"); counting("body", "parse_body"); counting("overview", "parse_overview_full"); counting("plan", "parse_plan_block")
    manuscript, plan = sample_pair
    run = run_all([str(manuscript), str(plan)])
    assert all(o.status == OK for o in run.outcomes.values())
    # 차례·필요지식이 함께 쓰는 toc/body, 개요·필요지식이 함께 쓰는 개요 파서 — 모두 1회
    assert calls == {"toc": 1, "body": 1, "overview": 1, "plan": 1}


def test_missing_body_section_fails_only_body_areas(tmp_path):
    front = manuscript_sections()[0]
    manuscript = write_hwpx(tmp_path / "원고_LM1203020201_24v3.hwpx", [front])  # 본문 섹션 없음
    run = run_documents(load_document(manuscript), None, config=ReviewConfig(areas=("toc", "overview", "knowledge")))
    assert run.outcomes["toc"].status == FAILED and "섹션" in run.outcomes["toc"].error
    assert run.outcomes["knowledge"].status == FAILED
    assert run.outcomes["overview"].status == OK  # 개요는 앞 섹션만 있으면 된다
