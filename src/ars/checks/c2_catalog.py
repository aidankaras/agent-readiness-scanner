import json
from . import result
from ..context import walk

NAME = "Catalog / endpoint access"


def ucp_endpoints(ctx):
    r = ctx.get("/.well-known/ucp")
    if not r.ok:
        return []
    try:
        u = json.loads(r.text).get("ucp")
    except Exception:
        return []
    if not isinstance(u, dict):
        return []
    # services may be a map of name -> [bindings] or a list of entries; take every binding with an endpoint
    return [b["endpoint"] for b in walk(u.get("services")) if isinstance(b.get("endpoint"), str) and b["endpoint"]]


def check(ctx):
    ev = []
    prod, sm = ctx.sitemap_product_urls()
    has_sitemap = bool(prod)
    if prod:
        ev.append(f"sitemap.xml: {len(prod)} product URLs")
    elif sm.ok:
        ev.append(f"sitemap.xml: HTTP {sm.status}, no product URLs")
    else:
        ev.append(f"sitemap.xml: HTTP {sm.status} (not available)")
    eps = ucp_endpoints(ctx)
    reachable = None
    if eps:
        ep = eps[0]
        r = ctx.get(ep)
        # MCP endpoints expect JSON-RPC POST, so a GET may get 405/400/401/403: the endpoint exists and answers.
        # 404/410 mean the declared path doesn't exist; 5xx and network errors mean it is down.
        reachable = 0 < r.status < 500 and r.status not in (404, 410)
        why = "answers" if reachable else "path not found" if r.status in (404, 410) else "unreachable"
        ev.append(f"UCP endpoint {ep} declared; GET probe HTTP {r.status} ({why}; protocol not exercised)")
    else:
        ev.append("no UCP endpoint declared")
    if ctx.is_shopify():
        ev.append("info: /products.json public (Shopify; not what agents consume)")
    if has_sitemap and reachable:
        st = "pass"
    elif has_sitemap or reachable:
        st = "partial"
    else:
        st = "fail"
    return result("c2", NAME, st, ev, "Publish product URLs in sitemap.xml and expose a reachable UCP endpoint (Shopify does this automatically for eligible stores).")
