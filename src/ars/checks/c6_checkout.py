import json
from . import result

NAME = "Checkout signals (UCP profile)"


def check(ctx):
    r = ctx.get("/.well-known/ucp")
    if not r.ok:
        return result("c6", NAME, "fail", [f"/.well-known/ucp: HTTP {r.status}"], "Publish a UCP profile at /.well-known/ucp (automatic on eligible Shopify stores; otherwise via Google's UCP integration).")
    if "html" in r.ctype.lower() or r.text.lstrip()[:1] == "<":
        return result("c6", NAME, "fail", ["/.well-known/ucp returned HTML (soft 404 or bot wall), not a UCP profile"], "Publish a UCP profile at /.well-known/ucp.")
    try:
        u = json.loads(r.text)["ucp"]
    except Exception:
        return result("c6", NAME, "partial", ["/.well-known/ucp present but not valid UCP JSON"], "Fix the UCP profile so it parses as JSON with a top-level 'ucp' object.")
    caps = set((u.get("capabilities") or {}).keys())
    svcs = set((u.get("services") or {}).keys())
    ev = [f"ucp.version {u.get('version')}", f"services {sorted(svcs)}", f"capabilities {sorted(caps)}"]
    has_buy = bool(caps & {"dev.ucp.shopping.checkout", "dev.ucp.shopping.cart"})
    st = "pass" if (u.get("version") and svcs and has_buy) else "partial"
    return result("c6", NAME, st, ev, "Declare dev.ucp.shopping.checkout and/or cart capabilities and a shopping service in the UCP profile.")
