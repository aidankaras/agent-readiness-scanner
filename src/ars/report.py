from .score import WEIGHTS

ICON = {"pass": "PASS", "partial": "PARTIAL", "fail": "FAIL", "info": "INFO"}


def markdown(res):
    out = [f"# Agent-readiness report: {res['url']}", "", f"**Score: {res['score']}/100** (scanner v{res['version']}, {res['scanned_at']}; weights are provisional)", ""]
    for c in res["checks"]:
        w = WEIGHTS.get(c["id"])
        out.append(f"## {ICON[c['status']]} {c['name']}" + (f" (weight {w})" if w else ""))
        out += [f"- {e}" for e in c["evidence"]]
        if c.get("fix"):
            out.append(f"\nFix: {c['fix']}")
        out.append("")
    return "\n".join(out)


def csv_rows(results):
    ids = list(WEIGHTS) + ["c7"]
    yield ["url", "score"] + ids
    for r in results:
        st = {c["id"]: c["status"] for c in r["checks"]}
        yield [r["url"], r["score"]] + [st.get(i, "") for i in ids]
