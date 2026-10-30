import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))  # hwpx_builder

from hwpx_builder import write_sample_pair  # noqa: E402


@pytest.fixture(scope="session")
def sample_pair(tmp_path_factory):
    return write_sample_pair(tmp_path_factory.mktemp("sample"))
