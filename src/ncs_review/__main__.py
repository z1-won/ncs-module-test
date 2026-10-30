"""python -m ncs_review …  — cli.main 과 같다."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
