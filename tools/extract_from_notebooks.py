"""노트북 배포본(write_module 셀)에서 패키지 소스를 꺼내 src/ 로 복원한다.

사용: python tools/extract_from_notebooks.py 노트북1.ipynb 노트북2.ipynb ... [--out src] [--prefer-newer]

- 각 노트북의 `# 모듈: <경로>` 셀을 실행해 write_module 호출을 가로챈다.
- 노트북 metadata.source_sha256 과 대조해 추출이 바이트 단위로 같은지 확인한다.
- 같은 경로가 여러 노트북에 다른 내용으로 있으면 충돌을 보고한다.
  --prefer-newer 를 주면 __init__.py 의 __version__ 이 큰 패키지의 파일 집합을 통째로 채택한다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"')


def modules_of(notebook: Path) -> dict[str, str]:
    data = json.loads(notebook.read_text(encoding="utf-8"))
    collected: dict[str, str] = {}

    def write_module(relative_path: str, source: str) -> None:
        collected[relative_path] = source

    for cell in data["cells"]:
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        if not source.lstrip().startswith("# 모듈:"):
            continue
        exec(compile(source, f"{notebook.name}:{cell.get('id', '?')}", "exec"), {"write_module": write_module})
    expected = data.get("metadata", {}).get("source_sha256", {})
    for path, text in collected.items():
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if path in expected and expected[path] != digest:
            raise SystemExit(f"{notebook.name}: {path} 의 sha256 이 노트북 메타데이터와 다름")
    return collected


def package_version(files: dict[str, str], package: str) -> tuple[int, ...]:
    init = files.get(f"{package}/__init__.py", "")
    match = VERSION_RE.search(init)
    return tuple(int(x) for x in match.groups()) if match else (0, 0, 0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebooks", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, default=Path("src"))
    parser.add_argument("--prefer-newer", action="store_true")
    args = parser.parse_args()

    # 패키지별로 (버전, 파일들, 출처) 후보를 모은다.
    candidates: dict[str, list[tuple[tuple[int, ...], dict[str, str], str]]] = {}
    for notebook in args.notebooks:
        files = modules_of(notebook)
        by_package: dict[str, dict[str, str]] = {}
        for path, text in files.items():
            by_package.setdefault(path.split("/")[0], {})[path] = text
        for package, package_files in by_package.items():
            candidates.setdefault(package, []).append((package_version(package_files, package), package_files, notebook.name))

    chosen: dict[str, str] = {}
    for package, versions in sorted(candidates.items()):
        distinct = {json.dumps(sorted(f.items())) for _, f, _ in versions}
        if len(distinct) > 1:
            summary = ", ".join(f"{'.'.join(map(str, v))}@{src}" for v, _, src in versions)
            if not args.prefer_newer:
                raise SystemExit(f"{package}: 노트북 간 내용이 다름 ({summary}). --prefer-newer 로 최신 버전을 채택하세요")
            version, files, source = max(versions, key=lambda t: t[0])
            print(f"{package}: 충돌 → {'.'.join(map(str, version))} ({source}) 채택  [{summary}]")
        else:
            version, files, source = versions[0]
            print(f"{package}: {'.'.join(map(str, version))} ({len(versions)}개 노트북에서 동일)")
        chosen.update(files)

    for path, text in sorted(chosen.items()):
        target = args.out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    print(f"{len(chosen)}개 파일 → {args.out}")


if __name__ == "__main__":
    sys.exit(main())
