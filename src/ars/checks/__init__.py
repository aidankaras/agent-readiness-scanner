"""Each check: fn(ctx) -> dict(id, name, status in pass|partial|fail|info, evidence:list[str], fix:str)."""


def result(cid, name, status, evidence, fix=""):
    return {"id": cid, "name": name, "status": status, "evidence": evidence, "fix": fix if status != "pass" else ""}


from .c1_page_data import check as c1
from .c2_catalog import check as c2
from .c3_completeness import check as c3
from .c4_policy import check as c4
from .c5_agent_access import check as c5
from .c6_checkout import check as c6
from .c7_ineligible import check as c7

ALL = [c1, c2, c3, c4, c5, c6, c7]
