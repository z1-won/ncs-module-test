from ncs_review.cli import main


def test_cli_runs_and_saves(sample_pair, tmp_path, capsys):
    manuscript, plan = sample_pair
    assert main([str(manuscript), str(plan), "--out", str(tmp_path), "--quiet"]) == 0
    out = capsys.readouterr().out
    assert '"module_code": "LM1203020201_24v3"' in out and "종합" in out
    assert list(tmp_path.glob("LM1203020201_24v3_*/LM1203020201_24v3_검수결과.zip"))


def test_cli_input_error_exits_2(tmp_path, capsys):
    missing = tmp_path / "없음.hwpx"
    missing.write_bytes(b"")
    try:
        main([str(missing), "--no-save"])
    except SystemExit as stop:
        assert stop.code == 2
    else:
        raise AssertionError("종료 코드 2 를 기대")
