import re
from . import result

NAME = "Checkout-ineligible flags (informational)"
PATTERNS = {"subscription": r"subscribe\s*(&|and)\s*save", "final sale": r"final\s+sale", "pre-order": r"pre-?order"}


def check(ctx):
    hits = []
    for url, r in ctx.product_pages():
        if r.ok:
            t = r.text
            for k, pat in PATTERNS.items():
                if re.search(pat, t, re.I):
                    hits.append(f"{url}: {k}")
    return {"id": "c7", "name": NAME, "status": "info", "evidence": hits or ["none detected"],
            "fix": "Google marks subscriptions, final-sale and pre-order items ineligible for agentic checkout; flag them in Merchant Center." if hits else ""}
