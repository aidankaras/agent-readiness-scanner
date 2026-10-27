import json
from . import result

NAME = "Catalog / endpoint access"


def ucp_endpoints(ctx):
    r = ctx.get("/.well-known/ucp")
    if not r.ok:
        return []
    try:
        svc = json.loads(r.text).get("ucp", {}).get("services", {})
    except Exception:
        return []
    return [b.get("endpoint") for v in svc.values() if isinstance(v, list) for b in v if isinstance(b, dict) and b.get("endpoint")]


def check(ctx):
    ev = []
    prod, sm = ctx.sitemap_product_urls()
    has_sitemap = bool(prod)
    ev.append(f"sitemap.xml: {'%d product URLs' % len(prod) if prod else ('HTTP %s' % sm.status if sm else 'no product URLs')}")
    eps = ucp_endpoints(ctx)
    reachable = None
    if eps:
        ep = eps[0]
        r = ctx.get(ep)
        # MCP endpoints expect JSON-RPC POST; a GET probe only proves the host answers. Count declared + host up.
        reachable = r.status > 0 and r.status < 500
        ev.append(f"UCP endpoint {ep} declared; GET probe HTTP {r.status} (host {'answers' if reachable else 'unreachable'}; protocol not exercised)")
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
