"""F02 검수 서비스 진입점. 원고(+개발계획서)를 한 번 읽어 차례·개요·필요지식·위치 검수를 함께 실행한다.

각 영역의 판정 로직은 ncs_toc / ncs_overview / ncs_knowledge / ncs_position 에 그대로 있고,
이 패키지는 그것들을 한 번의 실행으로 묶고(부분 실패 허용) 결과를 한 폴더에 모은다.
"""

__version__ = "0.2.0"  # 결과의 engine_version 에 기록된다. 규칙 변경 시 올린다.

from .areas import AREAS, Area  # noqa: E402
from .config import ReviewConfig  # noqa: E402
from .extract import ExtractedDocuments  # noqa: E402
from .orchestrator import AreaOutcome, RunResult, run_all, run_documents  # noqa: E402
from .reporting import SavedRun, save_run  # noqa: E402

__all__ = [
    "AREAS",
    "Area",
    "AreaOutcome",
    "ExtractedDocuments",
    "ReviewConfig",
    "RunResult",
    "SavedRun",
    "run_all",
    "run_documents",
    "save_run",
]
