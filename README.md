# ncs-review

NCS 학습모듈 원고(`.hwp` / `.hwpx`)를 F02 검수 확인서 기준으로 검사하는 엔진.
차례 · 학습모듈의 개요 · 필요 지식 · NCS-학습모듈의 위치 네 영역을 한 번에 실행하고 결과를 한 폴더에 모은다.
추가 설치 패키지 없이 Python 3.10 이상에서 동작한다.

```bash
pip install git+https://github.com/z1-won/ncs-module-test.git   # 또는 소스에서: pip install -e .
ncs-review 원고_LM1203020201_24v3.hwpx 개발계획서.hwp --out 결과
```

- 개발계획서가 없으면 위치 검수는 생략되고 나머지 영역은 계획서 대조만 생략(`-`)·판단불가(`△`)가 된다.
- 결과는 `결과/<모듈코드>_<실행>/` 아래 영역별 JSON과 `<코드>_00_종합요약.json`, `<코드>_검수결과.zip`.
- 판정 기호: `O` 충족 · `X` 위반 · `△` 사람 확인 · `-` 해당 없음. 행 판정은 X가 있으면 `부적합`, △만 있으면 `판단불가`, 나머지 `적합`.

구조와 이행 계획은 [docs/REFACTORING_PLAN.md](docs/REFACTORING_PLAN.md).

## Docker

```bash
docker compose build
docker compose run --rm review /data/원고_LM1203020201_24v3.hwpx /data/개발계획서.hwp
```

`./data` 가 `/data` 로, `./결과` 가 `/results` 로 마운트된다.

## 개발

```bash
pip install -e .[dev]
pytest
```

패키지 소스는 Colab 배포본 노트북에서 `tools/extract_from_notebooks.py` 로 복원했고, 노트북 메타데이터의 sha256 과 일치한다.
