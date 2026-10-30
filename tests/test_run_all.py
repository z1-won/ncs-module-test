import json

import pytest

from ncs_core import load_document
from ncs_review import AREAS, ReviewConfig, run_all, run_documents, save_run
from ncs_review.areas import Area
from ncs_review.orchestrator import FAILED, OK, SKIPPED


def test_all_areas_run_on_sample(sample_pair):
    manuscript, plan = sample_pair
    run = run_all([str(plan), str(manuscript)])  # 순서 무관
    assert run.module_code == "LM1203020201_24v3"
    assert {k: o.status for k, o in run.outcomes.items()} == {k: OK for k in AREAS}
    summary = run.summary()
    assert summary["failed"] == [] and summary["skipped"] == []
    assert summary["검수결과"] in ("적합", "부적합", "판단불가")
    assert summary["engine_version"]
    # 각 영역이 실제로 행을 냈다
    for outcome in run.outcomes.values():
        assert outcome.result.checklist


def test_without_plan_position_is_skipped(sample_pair):
    manuscript, _ = sample_pair
    run = run_all([str(manuscript)])
    assert run.outcomes["position"].status == SKIPPED
    assert all(run.outcomes[k].status == OK for k in ("toc", "overview", "knowledge"))


def test_failed_area_does_not_block_others(sample_pair):
    manuscript, plan = sample_pair
    docs = {"m": load_document(manuscript), "p": load_document(plan)}

    def boom(*args, **kwargs):
        raise RuntimeError("일부러 낸 오류")

    broken = dict(AREAS)
    broken["toc"] = Area("toc", "차례", "F02-차례-", False, boom, AREAS["toc"].evaluate, AREAS["toc"].save)
    run = run_documents(docs["m"], docs["p"], areas=broken)
    assert run.outcomes["toc"].status == FAILED
    assert "내부 오류" in run.outcomes["toc"].error and run.outcomes["toc"].traceback
    assert run.outcomes["overview"].status == OK
    assert run.verdict in ("부적합", "판단불가")  # 실패가 있으면 적합이라 하지 않는다


def test_save_run_writes_one_folder(sample_pair, tmp_path):
    manuscript, plan = sample_pair
    run = run_all([str(manuscript), str(plan)], config=ReviewConfig(areas=("toc", "overview")))
    saved = save_run(run, tmp_path / "결과")
    names = {p.name for p in saved.directory.iterdir()}
    assert "LM1203020201_24v3_00_종합요약.json" in names
    assert "LM1203020201_24v3_차례_00_요약.json" in names and "LM1203020201_24v3_개요_00_요약.json" in names
    assert saved.zip_path.exists()
    summary = json.loads((saved.directory / "LM1203020201_24v3_00_종합요약.json").read_text(encoding="utf-8"))
    assert set(summary["영역"]) == {"toc", "overview"}


def test_unknown_area_is_rejected(sample_pair):
    manuscript, _ = sample_pair
    with pytest.raises(ValueError):
        run_all([str(manuscript)], config=ReviewConfig(areas=("nope",)))
