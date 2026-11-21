import json
from ._result import result

NAME = "Checkout signals (UCP profile)"


def names(x):
    """Entry names from a UCP map ({name: ...}) or list ([{"name": ...}] or ["name"]); anything else -> empty."""
    if isinstance(x, dict):
        return {str(k) for k in x}
    if isinstance(x, list):
        return {str(i.get("name")) if isinstance(i, dict) else str(i) for i in x
                if (isinstance(i, dict) and i.get("name")) or isinstance(i, str)}
    return set()


def check(ctx):
    r = ctx.get("/.well-known/ucp")
    if not r.ok:
        return result("c6", NAME, "fail", [f"/.well-known/ucp: HTTP {r.status}"], "Publish a UCP profile at /.well-known/ucp (automatic on eligible Shopify stores; otherwise via Google's UCP integration).")
    if "html" in r.ctype.lower() or r.text.lstrip()[:1] == "<":
        return result("c6", NAME, "fail", ["/.well-known/ucp returned HTML (soft 404 or bot wall), not a UCP profile"], "Publish a UCP profile at /.well-known/ucp.")
    try:
        u = json.loads(r.text)["ucp"]
    except Exception:
        u = None
    if not isinstance(u, dict):
        return result("c6", NAME, "partial", ["/.well-known/ucp present but not valid UCP JSON"], "Fix the UCP profile so it parses as JSON with a top-level 'ucp' object.")
    caps, svcs = names(u.get("capabilities")), names(u.get("services"))
    ev = [f"ucp.version {u.get('version')}", f"services {sorted(svcs)}", f"capabilities {sorted(caps)}"]
    has_buy = bool(caps & {"dev.ucp.shopping.checkout", "dev.ucp.shopping.cart"})
    st = "pass" if (u.get("version") and svcs and has_buy) else "partial"
    return result("c6", NAME, st, ev, "Declare dev.ucp.shopping.checkout and/or cart capabilities and a shopping service in the UCP profile.")
