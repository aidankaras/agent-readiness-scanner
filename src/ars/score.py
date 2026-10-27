from datetime import datetime, timezone
from . import __version__
from .checks import ALL
from .context import Ctx

# v0.3 (after M2 Shopify sample): checks every Shopify store passes by default (c2,c5,c6) weigh less;
# merchant-controlled content (c3,c4) weighs more. Still provisional.
WEIGHTS = {"c1": 15, "c2": 10, "c3": 30, "c4": 20, "c5": 10, "c6": 15}
VALUE = {"pass": 1.0, "partial": 0.5, "fail": 0.0}


def scan(url, fetcher=None, now=None):
    ctx = Ctx(url, fetcher)
    checks = []
    for fn in ALL:
        try:
            checks.append(fn(ctx))
        except Exception as e:  # a broken check must not kill the scan
            checks.append({"id": fn.__module__.split(".")[-1][:2], "name": fn.__module__, "status": "fail", "evidence": [f"check error: {type(e).__name__}: {e}"], "fix": ""})
    score = sum(WEIGHTS[c["id"]] * VALUE.get(c["status"], 0) for c in checks if c["id"] in WEIGHTS)
    return {"url": ctx.base, "score": round(score, 1), "checks": checks,
            "scanned_at": now or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "version": __version__}
