# F02 검수 엔진 리팩토링 계획

작성: 2026-10-30 · 대상: Colab 노트북 배포본 4개 → 집필진 대상 검수 서비스의 엔진 패키지

## 0. 출발점 — 노트북 4개의 실제 상태

| 노트북 | 패키지 | 버전 | 포함 패키지 | 검수 항목 |
|---|---|---|---|---|
| `F02_차례_검수_v2_1.ipynb` | `ncs_toc` | 2.1.0 | ncs_core 1.0.0 | 차례 ①③⑤⑥ |
| `F02_개요_검수_v1_1.ipynb` | `ncs_overview` | 1.0.0 | ncs_core | 개요 ①②⑤⑥⑧ |
| `F02_필요지식_검수_v2_0.ipynb` | `ncs_knowledge` | 2.0.0 | ncs_core, **ncs_toc 2.2.0**, ncs_overview | 필요지식 ①~⑧ |
| `NCS_위치검수_v1_3.ipynb` | `ncs_position` | 1.3.0 | ncs_core | 위치 ①~⑤ |

노트북은 `tools/build_notebook.py`가 `src/` 패키지에서 생성한 배포본이고, 각 모듈 셀은 `write_module(경로, 소스)`로 임시 폴더에 패키지를 복원한다. 노트북 메타데이터 `source_sha256`에 파일별 해시가 있어 **추출 결과를 바이트 단위로 검증**할 수 있다.

이미 드러난 문제:

1. **엔진 버전 불일치.** 차례 노트북의 `ncs_toc`는 2.1.0, 필요지식 노트북에 동봉된 `ncs_toc`는 2.2.0(④ `rules/placement.py` 추가, `parse_toc`에 `after` 필드). 같은 원고를 노트북에 따라 다른 규칙으로 검수한다. 2.2.0은 2.1.0의 상위 집합이므로 2.2.0을 채택한다.
2. **중복 읽기.** 네 노트북이 같은 원고·계획서를 각각 읽고(`select_documents`), 차례·개요·본문·계획서 블록을 각각 파싱한다. `ncs_knowledge.pipeline`이 `ncs_toc.parsers`·`ncs_overview.parsers`를 가져다 쓰는 것이 "한 번 추출해 공유"가 필요하다는 신호다.
3. **결과 분산.** 결과 ZIP이 영역별로 4개 나오고, 한 원고의 F02 종합 판정은 사람이 합쳐야 한다. `△`(판단불가) 항목의 사람 확정을 기록할 곳이 없다.
4. **Colab 결합.** 입력·출력 셀이 `google.colab.files`에 묶여 있어 다른 환경에서 그대로 못 돌린다.
5. **테스트 부재.** 배포본 어디에도 자동 테스트가 없다.

설계 자체(core / parsers / rules / registry / reporting 분리, `ReviewContext` 경계, O/X/△/- 판정과 적합/부적합/판단불가 종합)는 그대로 가져간다. 이 계획은 **판정 정책을 바꾸지 않는다.** 같은 입력에 같은 JSON이 나와야 한다.

## 1. 목표 구조

```
ncs-review/
├─ pyproject.toml              # 배포 단위 하나: ncs-review (패키지 6개 포함), 의존성 없음(표준 라이브러리)
├─ src/
│   ├─ ncs_core/               # 문서 읽기(hwp/hwpx), Document·Table, 정규화·판정, 입력 역할, 모듈 코드, 저장  (그대로)
│   ├─ ncs_toc/                # 차례 ①③④⑤⑥                                   (2.2.0 그대로)
│   ├─ ncs_overview/           # 개요 ①②⑤⑥⑧                                   (그대로)
│   ├─ ncs_knowledge/          # 필요지식 ①~⑧                                   (그대로)
│   ├─ ncs_position/           # 위치 ①~⑤                                       (그대로)
│   └─ ncs_review/             # [신규] 서비스 진입점
│        ├─ config.py          #   ReviewConfig: 섹션·영역별 임계값 한 곳
│        ├─ extract.py         #   ExtractedDocuments: 모든 추출물을 지연·캐시로 1회
│        ├─ areas.py           #   영역 정의: 추출물 → 패키지 ReviewContext 어댑터, evaluate/save 연결
│        ├─ orchestrator.py    #   run_all(): 문서 1회 읽기 → 추출 1회 → 4영역 독립 실행(부분 실패 허용) → 종합 요약
│        ├─ reporting.py       #   결과/<코드>_<실행>/ 아래 영역별 파일 + 00_종합요약.json + ZIP
│        └─ cli.py             #   ncs-review 명령 (python -m ncs_review)
├─ tools/
│   └─ make_golden.py              # 실제 원고 쌍의 결과를 골든 JSON으로 저장
├─ tests/                      # pytest: 순수 함수, 합성 hwpx 로더, 오케스트레이터 스모크, 추출 무결성
├─ docs/REFACTORING_PLAN.md    # 이 문서
├─ Dockerfile · docker-compose.yml · .dockerignore
└─ .github/workflows/ci.yml    # pytest + docker build
```

### 왜 기존 패키지를 합치지 않고 그대로 두는가

1단계의 원칙은 "이동만, 변경 없음"이다. 임포트 경로(`ncs_core`, `ncs_toc` …)를 유지하면 노트북에서 검증된 동작이 그대로 보존되고, `source_sha256`으로 추출이 정확함을 증명할 수 있다. 통합(단일 `ReviewContext`, 추출 1회)은 2단계에서 **테스트가 깔린 뒤** 한다.

## 2. 단계

### 1단계 — 패키지화 — **완료 (v0.1.0)**

| # | 작업 | 산출물 | 확인 방법 |
|---|---|---|---|
| 1-1 | 노트북에서 소스 추출, 해시 검증, `ncs_toc` 2.2.0 채택 | `src/ncs_*` 79개 파일 | `tools/extract_from_notebooks.py --prefer-newer` 가 메타데이터 해시와 일치 |
| 1-2 | `pyproject.toml` (src 레이아웃, 표준 라이브러리만) | 설치 가능한 `ncs-review` | `pip install -e .` 후 `python -c "import ncs_toc, ncs_overview, ncs_knowledge, ncs_position"` |
| 1-3 | 오케스트레이터 `ncs_review.run_all` | 원고(+계획서) 1회 읽기, 영역별 `status: ok/failed/skipped`, 종합 `검수결과` | 합성 hwpx로 스모크 테스트 |
| 1-4 | CLI `ncs-review` | 노트북 4개를 명령 1개로 대체 | `ncs-review 원고.hwpx 계획서.hwp --out 결과` |
| 1-5 | 테스트 | `tests/` | `pytest` 통과, CI |
| 1-6 | Docker | `Dockerfile`, `docker-compose.yml` | `docker build` 후 `docker run … --help` |
| 1-7 | git/GitHub | 단계별 커밋, CI 워크플로 | 원격 푸시 |
| 1-8 | ~~Colab 클라이언트 노트북~~ | — | 당장 쓰지 않아 삭제. 노트북 원본·추출 도구는 첫 커밋 `5f4c150`에 남아 있음 |

오케스트레이터의 규칙:

- 입력은 `ncs_core.select_documents`로 **한 번** 읽는다. 위치 검수는 계획서가 필수이므로 계획서가 없으면 `skipped`.
- 각 영역은 `try/except`로 격리한다. 한 영역의 `ValueError`(양식 불일치, 섹션 없음)가 다른 영역 결과를 막지 않는다. 오류 메시지는 이미 한국어 사용자 문장이므로 그대로 결과에 싣는다.
- 종합 판정은 `ncs_core.reporting.overall_verdict`와 같은 규칙(부적합 > 판단불가 > 적합). 실패한 영역이 있으면 종합은 `판단불가`로 내리고 `failed` 목록을 적는다.
- 결과 폴더는 `결과/<모듈코드>_<실행별>/` 하나. 안에 기존 영역별 파일(이름 규칙 불변)과 `<코드>_00_종합요약.json`, `<코드>_검수결과.zip`. 기존 영역별 ZIP 소비자가 있으면 그대로 쓸 수 있도록 영역별 파일 이름은 바꾸지 않는다.

### 2단계 — 통합 파이프라인 (판정 불변, 구조 변경) — **완료 (v0.2.0)**

- `ncs_review/extract.py` `ExtractedDocuments`: 네 영역이 쓰는 모든 추출물(toc, toc_overview, plan_toc, presence, body, eval_tables, overview, plan_info, structure, units, plan_goals, table_paragraphs, labels, 분류·위치 표·서식 표·계획서 모듈명)을 **지연·캐시 속성**으로 한 번만 만든다. 차례·필요지식이 함께 쓰던 `parse_toc`/`parse_body`, 개요·필요지식이 함께 쓰던 개요 파서가 각 1회 호출된다(`tests/test_extract.py`).
- 각 패키지의 `ReviewContext`는 `ncs_review/areas.py`의 어댑터가 추출물로 조립하고, 기존 `evaluate_review`를 그대로 호출한다. 규칙 모듈·파서는 한 줄도 바꾸지 않았다. 패키지별 `prepare_review`는 단독 사용을 위해 남겨 둔다.
- 추출 실패는 그 추출물을 쓰는 영역에만 전파된다(본문 섹션이 없으면 차례·필요지식만 실패, 개요는 정상).
- `ncs_review/config.py` `ReviewConfig`가 섹션 번호와 영역별 임계값(차례 휴리스틱 5개, 개요 3개, 필요지식 6개)을 한 곳에서 갖고 각 패키지 `CheckConfig`를 만든다. 기본값은 기존과 같다.
- 회귀 기준: 실제 원고 LM1203020201_24v3 의 골든(`tests/golden/`, 158행·지적 66건)과 통합 후 출력이 같다. `engine_version`만 비교에서 뺀다.
- 미착수: 교차 참조 정리(개요 ⑤ 비고의 "차례 ③ 참조", 기호 글꼴 중복 보고). 규칙 변경이 필요하므로 판정 변경 커밋으로 따로 한다.

### 3단계 — 서비스 (별도 저장소 또는 `apps/`)

- API(FastAPI): `POST /submissions`(원고·계획서) → `job_id`, `GET /runs/{id}`, 결과 JSON/xlsx 다운로드.
- 워커(RQ/Celery): `ncs_review.run_all` 호출. hwp 파싱은 CPU 작업이므로 요청 스레드에서 분리.
- 저장: Postgres(`Module, Submission, Run, Finding, Decision, User`), 객체 저장소(원고·결과).
- `Run`에 엔진 버전(`ncs_review.__version__`)과 설정을 기록해 규칙 변경 뒤 재검수 추적.
- 집필진 UI: 지적사항 목록(부적합→판단불가, `region_path`·원문 인용), **재제출 비교**(`(item_id, check, region_path)` 키로 해결됨/그대로/새로 생김).
- 검수자 UI: △ 확정(확인/오탐/수정완료) + 메모 → `Decision`.
- 요구사항정의서(V0.20) 기준: REQ-02-002/003 입력은 HWPX, 결과는 "오류·누락·불일치 후보 제시"; REQ-02-007이 개별 검수 결과를 통합(화면/PDF). 종합요약 JSON이 REQ-02-007의 입력이 된다.

### 보류·후속

- 검수 확인서(F02) 형식의 xlsx 내보내기: 양식 확정 후 `ncs_review.reporting`에 추가.
- hwp(바이너리) 업로드 정책: 위치 ⑤·필요지식 ⑥⑧이 제한되므로 서비스에서 hwpx 권장 안내. 서버 측 hwp→hwpx 변환은 한컴 환경 없이는 불가.
- 미구현 항목(차례 ②⑦, 개요 ③④⑦, 수행내용·교수학습·평가·참고자료·기타)은 프로젝트 문서 `PoC2_정리_파일지도_F02항목별.md`의 매트릭스대로 규칙 모듈을 추가. 구조는 이미 `registry`에 `Rule`을 더하는 것으로 충분하다.
- 별도 계보(이미지 해상도 `image_quality`, 수행내용 `perform_124`)는 같은 `Rule` 계약으로 옮겨 `ncs_review.areas`에 영역을 추가한다.

## 3. 하지 않는 것

- 판정 정책 변경(임계값, X/△ 기준). 변경은 테스트와 함께 별도 커밋으로.
- 규칙 모듈 재작성. 1·2단계 모두 `rules/` 내용은 그대로.
- Colab 노트북 유지. 노트북 원본과 추출 도구는 git 역사(`5f4c150`)에만 남긴다.
