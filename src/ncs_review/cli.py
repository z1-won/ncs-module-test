"""ncs-review 원고.hwpx [개발계획서.hwp] [--areas toc,overview] [--module-code LM...] [--out 결과]

노트북 4개(차례·개요·필요지식·위치)를 명령 하나로 대체한다. 종료 코드: 0 정상, 2 입력 오류.
"""

import argparse
import json
import sys

from . import __version__
from .areas import AREAS
from .config import ReviewConfig
from .orchestrator import run_all
from .reporting import save_run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ncs-review", description="NCS 학습모듈 F02 검수 (차례·개요·필요지식·위치)")
    parser.add_argument("paths", nargs="+", help="원고와 (선택) 개발계획서. 순서 무관, 내용으로 역할 판별")
    parser.add_argument("--manuscript", help="자동 역할 판별 대신 원고로 지정할 입력 경로")
    parser.add_argument("--plan", help="자동 역할 판별 대신 개발계획서로 지정할 입력 경로")
    parser.add_argument("--module-code", default="", help="비우면 원고 파일명에서 추출 (예: LM1203020201_24v3)")
    parser.add_argument("--areas", default=",".join(AREAS), help=f"쉼표로 나눈 영역 (기본: 전부). 가능: {', '.join(AREAS)}")
    parser.add_argument("--front-section", type=int, default=0, help="차례·개요·위치 섹션 (기본 0)")
    parser.add_argument("--body-section", type=int, default=1, help="본문 섹션 (기본 1)")
    parser.add_argument("--out", default="결과", help="결과 폴더 (실행마다 하위 폴더 생성)")
    parser.add_argument("--no-save", action="store_true", help="파일로 저장하지 않고 요약만 출력")
    parser.add_argument("--quiet", action="store_true", help="지적사항 목록을 출력하지 않음")
    parser.add_argument("--version", action="version", version=f"ncs-review {__version__}")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    roles = {}
    if args.manuscript:
        roles[args.manuscript] = "manuscript"
    if args.plan:
        roles[args.plan] = "plan"
    try:
        config = ReviewConfig(
            front_section=args.front_section,
            body_section=args.body_section,
            areas=tuple(a.strip() for a in args.areas.split(",") if a.strip()),
        )
        run = run_all(args.paths, roles=roles, module_code=args.module_code, config=config)
        saved = None if args.no_save else save_run(run, args.out)
    except (OSError, ValueError) as error:
        parser.exit(2, f"검수 실행 실패: {error}\n")
    print(json.dumps(run.summary(), ensure_ascii=False, indent=2))
    if not args.quiet:
        for finding in run.findings:
            print(f"{finding['item_id']} | {finding['check']} | {finding['reason']}")
    print(f"지적사항 {len(run.findings)}건 · 종합 {run.verdict}" + (f" · {saved.zip_path}" if saved else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
