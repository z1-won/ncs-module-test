# ncs-review: F02 검수 엔진 CLI 이미지. 표준 라이브러리만 쓰므로 slim 베이스로 충분하다.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    LANG=C.UTF-8

WORKDIR /app

# 의존성 층(현재는 빌드 도구뿐) — 소스가 바뀌어도 캐시된다
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install .

# 실행 전용 사용자. 입력은 /data, 결과는 /results 에 마운트한다.
RUN useradd --create-home --uid 1000 reviewer \
    && mkdir -p /data /results \
    && chown reviewer:reviewer /data /results
USER reviewer
VOLUME ["/data", "/results"]

ENTRYPOINT ["ncs-review"]
CMD ["--help"]


# 테스트 층: docker build --target test .  (CI 가 사용)
FROM base AS test
USER root
COPY tests ./tests

RUN pip install pytest
USER reviewer
CMD ["python", "-m", "pytest", "-q"]
