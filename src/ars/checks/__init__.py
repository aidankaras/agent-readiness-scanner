"""Each check: fn(ctx) -> dict(id, name, status in pass|partial|fail|info, evidence:list[str], fix:str)."""

from ._result import result  # noqa: F401  (re-exported for callers of ars.checks.result)
from .c1_page_data import check as c1
from .c2_catalog import check as c2
from .c3_completeness import check as c3
from .c4_policy import check as c4
from .c5_agent_access import check as c5
from .c6_checkout import check as c6
from .c7_ineligible import check as c7

ALL = [c1, c2, c3, c4, c5, c6, c7]
