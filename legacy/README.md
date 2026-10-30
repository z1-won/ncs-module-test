# legacy/

리팩토링 전 Colab 배포본 노트북 원본. `src/` 는 이 노트북들에서 `tools/extract_from_notebooks.py` 로 복원했고,
`tests/test_extraction.py` 가 복원 결과와 `src/` 가 같은지(노트북 메타데이터 sha256 기준) 확인한다.

| 노트북 | 패키지 | 비고 |
|---|---|---|
| `F02_차례_검수_v2_1.ipynb` | ncs_toc 2.1.0 | `ncs_toc` 는 필요지식 노트북의 2.2.0(④ 추가)을 채택 |
| `F02_개요_검수_v1_1.ipynb` | ncs_overview 1.0.0 | |
| `F02_필요지식_검수_v2_0.ipynb` | ncs_knowledge 2.0.0 (+ ncs_toc 2.2.0, ncs_overview) | |
| `NCS_위치검수_v1_3.ipynb` | ncs_position 1.3.0 | |

이 노트북들은 더 이상 갱신하지 않는다. Colab 에서는 `notebooks/F02_검수_클라이언트.ipynb` 를 쓴다.
