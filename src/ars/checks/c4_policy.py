import re
from . import result
from .c3_completeness import strip

NAME = "Policy clarity"
CANDIDATES = {
    "returns": ["/policies/refund-policy", "/refund-policy", "/refund_returns", "/shipping-returns", "/pages/returns", "/returns", "/pages/return-policy", "/return-policy"],
    "shipping": ["/policies/shipping-policy", "/shipping-policy", "/delivery", "/shipping-returns", "/pages/shipping", "/shipping", "/pages/shipping-policy"],
    "contact": ["/pages/contact", "/policies/contact-information", "/contact", "/pages/contact-us", "/contact-us"],
}
LINK_RE = re.compile(r'href=["\']([^"\'#]+)["\']', re.I)
WORDS = {"returns": r"return|refund|exchange", "shipping": r"shipping|delivery|postage", "contact": r"contact|about"}


def find(ctx, kind, home_links):
    linked = [l for l in dict.fromkeys(home_links) if re.search(WORDS[kind], l, re.I)][:4]
    paths = linked + [p for p in CANDIDATES[kind] if p not in linked]
    for p in paths:
        r = ctx.get(p)
        if r.ok and len(strip(r.text)) > 200:
            return p, strip(r.text)
    return None, ""


def check(ctx):
    home = ctx.get("/")
    links = []
    for l in LINK_RE.findall(home.text if home.ok else ""):
        if l.startswith(ctx.base):
            l = l[len(ctx.base):]
        if l.startswith("/") and not l.startswith("//"):
            links.append(l)
    ev, got = [], 0
    ret_text = ""
    for kind in ("returns", "shipping", "contact"):
        p, txt = find(ctx, kind, links)
        ev.append(f"{kind}: {p or 'not found'}")
        got += bool(p)
        if kind == "returns":
            ret_text = txt
    window = bool(re.search(r"\b\d{1,3}\s*(-|\s)?\s*(day|days)\b", ret_text, re.I))
    ev.append(f"return window stated: {'yes' if window else 'no'}")
    pts = got + window
    st = "pass" if pts == 4 else "partial" if pts >= 2 else "fail"
    return result("c4", NAME, st, ev, "Publish reachable returns (with window in days and cost), shipping, and contact pages; Google requires return window/cost/link and a support contact for agentic checkout.")
