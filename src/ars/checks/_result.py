def result(cid, name, status, evidence, fix=""):
    """Build a check record; fix text is dropped on a pass."""
    return {"id": cid, "name": name, "status": status, "evidence": evidence, "fix": fix if status != "pass" else ""}
