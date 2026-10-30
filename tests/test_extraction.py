"""legacy/notebooks 에서 복원한 소스가 src/ 와 같은지 — 노트북 메타데이터 sha256 기준."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = sorted((ROOT / "legacy" / "notebooks").glob("*.ipynb"))
TOC_22_SOURCE = "F02_필요지식_검수_v2_0.ipynb"  # ncs_toc 는 이 노트북의 2.2.0 을 채택했다


def test_src_matches_notebook_hashes():
    assert NOTEBOOKS, "legacy/notebooks 가 비어 있음"
    checked = 0
    for notebook in NOTEBOOKS:
        expected = json.loads(notebook.read_text(encoding="utf-8"))["metadata"]["source_sha256"]
        for path, digest in expected.items():
            if path.startswith("ncs_toc/") and notebook.name != TOC_22_SOURCE:
                continue  # 2.1.0 은 의도적으로 채택하지 않음
            actual = hashlib.sha256((ROOT / "src" / path).read_bytes()).hexdigest()
            assert actual == digest, f"{path} 가 {notebook.name} 의 소스와 다름"
            checked += 1
    assert checked >= 79
