"""테스트용 합성 hwpx 생성기. ncs_core.hwpx 가 읽는 최소 구조(section XML + header.xml)만 만든다.

실제 한컴 문서가 아니라 로더·파서·규칙이 끝까지 도는지 확인하는 용도다.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HH = "http://www.hancom.co.kr/hwpml/2011/head"
HC = "http://www.hancom.co.kr/hwpml/2011/core"

# charPr id: 0 보통(함초롬바탕), 1 굵게 KoPub돋움체 / borderFill id: 1 없음, 2 노랑 음영
HEADER_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<hh:head xmlns:hh="{HH}" xmlns:hc="{HC}">
  <hh:refList>
    <hh:fontfaces>
      <hh:fontface lang="HANGUL"><hh:font id="0" face="함초롬바탕"/><hh:font id="1" face="KoPub돋움체"/></hh:fontface>
    </hh:fontfaces>
    <hh:borderFills>
      <hh:borderFill id="1"><hc:fillBrush><hc:winBrush faceColor="none"/></hc:fillBrush></hh:borderFill>
      <hh:borderFill id="2"><hc:fillBrush><hc:winBrush faceColor="#FFFF00"/></hc:fillBrush></hh:borderFill>
    </hh:borderFills>
    <hh:charProperties>
      <hh:charPr id="0"><hh:fontRef hangul="0"/></hh:charPr>
      <hh:charPr id="1"><hh:fontRef hangul="1"/><hh:bold/></hh:charPr>
    </hh:charProperties>
  </hh:refList>
</hh:head>
"""


def p(text: str, char: int = 0) -> str:
    return f'<hp:p><hp:run charPrIDRef="{char}"><hp:t>{escape(text)}</hp:t></hp:run></hp:p>'


def table(rows: list[list[str | tuple[str, int, int]]]) -> str:
    """셀은 문자열 또는 (텍스트, charPr, borderFill). 표는 빈 문단 안에 들어간다."""
    out = [f'<hp:p><hp:run><hp:tbl rowCnt="{len(rows)}" colCnt="{len(rows[0])}">']
    for r, row in enumerate(rows):
        out.append("<hp:tr>")
        for c, cell in enumerate(row):
            text, char, fill = cell if isinstance(cell, tuple) else (cell, 0, 1)
            out.append(
                f'<hp:tc borderFillIDRef="{fill}"><hp:cellAddr rowAddr="{r}" colAddr="{c}"/>'
                f"<hp:subList>{p(text, char)}</hp:subList></hp:tc>"
            )
        out.append("</hp:tr>")
    out.append("</hp:tbl></hp:run></hp:p>")
    return "".join(out)


def section(items: list[str]) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="{HP}">' + "".join(items) + "</hs:sec>"


def write_hwpx(path: Path, sections: list[list[str]], *, header: bool = True) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/hwp+zip")
        if header:
            archive.writestr("Contents/header.xml", HEADER_XML)
        for index, items in enumerate(sections):
            archive.writestr(f"Contents/section{index}.xml", section(items))
    return path


# ---------------------------------------------------------------- 표본 원고·계획서

CODE = "1203020201_24v3"
MODULE_CODE = "LM" + CODE
BOX1 = "\U000F02B1"  # 한글 기호 글꼴 ‘󰊱’ (필요지식 ⑥ 첫 수준)


def manuscript_sections() -> list[list[str]]:
    front = [
        p("차 례"),
        p("학습 1. 객실 예약 접수하기 12"),
        p("1-1. 예약 접수 13"),
        p("1-2. 예약 변경 20"),
        p("• 교수·학습 방법 25"),
        p("• 평가 26"),
        p("학습 2. 객실 예약 관리하기 30"),
        p("2-1. 예약 현황 관리 31"),
        p("• 교수·학습 방법 35"),
        p("• 평가 36"),
        p("참고 자료 40"),
        p("[NCS-학습모듈의 위치]"),
        table([["대분류", "중분류", "소분류"], ["음식서비스", "숙박", "숙박 서비스"]]),
        table([
            ["세분류", "능력단위", "학습모듈명"],
            [("호텔 운영", 0, 2), ("객실 예약 접수", 1, 2), ("객실 예약 접수", 1, 2)],
            ["", "객실 예약 관리", "객실 예약 관리"],
            ["카지노 운영", "카지노 딜링", "카지노 딜링"],
        ]),
        p("학습모듈의 개요"),
        p("학습모듈의 목표"),
        p("고객의 요청에 따라 객실 예약을 접수하고 관리할 수 있다."),
        p("선수 학습"),
        p("호텔 경영론, 서비스 실무"),
        p("학습모듈의 내용 체계"),
        table([
            ["학습", "학습 내용", "코드번호", "요소 명칭"],
            ["1. 객실 예약 접수하기", "1-1. 예약 접수", f"{CODE}.1", "객실 예약 접수하기"],
            ["", "1-2. 예약 변경", "", ""],
            ["2. 객실 예약 관리하기", "2-1. 예약 현황 관리", f"{CODE}.2", "객실 예약 관리하기"],
        ]),
        p("핵심 용어"),
        p("예약, 체크 인(Check In, 투숙), 객실"),
    ]
    nav = [p("학습 1"), p("객실 예약 접수하기"), p("학습 2"), p("객실 예약 관리하기")]
    eval_table = lambda *names: table([["학습 내용", "학습 목표", "평가 항목"], *[[n, "목표", "항목 여부"] for n in names]])
    body = [
        *nav,
        p("1-1. 예약 접수"),
        p("학습 목표"),
        p("• 고객의 예약 요청을 접수할 수 있다."),
        p("필요 지식"),
        p(f"{BOX1} 예약의 개념"),
        p("1. 예약의 정의"),
        p("(1) 사전 예약"),
        p("(2) 당일 예약"),
        p("2. 예약 채널"),
        p("출처: 집필진 제작(2026)"),
        p("[그림 1-1] 예약 처리 흐름"),
        p("[그림 1-1]과 같이 예약은 접수에서 시작한다."),
        p("1-2. 예약 변경"),
        p("학습 목표"),
        p("• 예약을 변경할 수 있다."),
        p("필요 지식"),
        p(f"{BOX1} 변경 절차"),
        p("교수·학습 방법"),
        p("평 가"),
        eval_table("예약 접수", "예약 변경"),
        *nav,
        p("2-1. 예약 현황 관리"),
        p("학습 목표"),
        p("• 예약 현황을 관리할 수 있다."),
        p("필요 지식"),
        p(f"{BOX1} 현황 관리"),
        p("출처: 홍길동(2024). 호텔 경영. 한빛. p.12."),
        p("[그림 2-1] 예약 현황판"),
        p("교수·학습 방법"),
        p("평 가"),
        eval_table("예약 현황 관리"),
        p("참고 자료"),
        p("• 홍길동(2024). 호텔 경영. 한빛."),
        p("• 김철수(2023). 서비스 실무. 교문사."),
        p("• 이영희(2022). 숙박 운영론. 학지사."),
        p("개발 이력"),
    ]
    return [front, body]


def plan_sections() -> list[list[str]]:
    return [[
        p("학습모듈 개발계획서"),
        table([["대분류", "중분류", "소분류"], ["음식서비스", "숙박", "숙박 서비스"]]),
        table([
            ["세분류", "능력단위", "학습모듈명"],
            ["호텔 운영", "객실 예약 접수", "객실 예약 접수"],
            ["", "객실 예약 관리", "객실 예약 관리"],
            ["카지노 운영", "카지노 딜링", "카지노 딜링"],
        ]),
        p("능력단위 코드번호"),
        p(CODE),
        p("학습 모듈명"),
        p("객실 예약 접수"),
        p("능력단위 정의"),
        p("객실 예약 접수란 고객의 요청에 따라 객실 예약을 접수하고 관리하는 능력이다."),
        p("학습모듈의 목표"),
        p("고객의 요청에 따라 객실 예약을 접수하고 관리할 수 있다."),
        p(f"{CODE}.1"),
        p("객실 예약 접수하기"),
        p("1. 객실 예약 접수하기"),
        p("1-1. 예약 접수"),
        p("1.1 고객의 예약 요청을 접수할 수 있다."),
        p("1-2. 예약 변경"),
        p("1.2 예약을 변경할 수 있다."),
        p(f"{CODE}.2"),
        p("객실 예약 관리하기"),
        p("2. 객실 예약 관리하기"),
        p("2-1. 예약 현황 관리"),
        p("2.1 예약 현황을 관리할 수 있다."),
        p("NCS (수정 금지)"),
    ]]


def write_sample_pair(directory: Path) -> tuple[Path, Path]:
    manuscript = write_hwpx(directory / f"원고_{MODULE_CODE}.hwpx", manuscript_sections())
    plan = write_hwpx(directory / "개발계획서.hwpx", plan_sections())
    return manuscript, plan
