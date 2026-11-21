import re, urllib.parse
from ._result import result
from ..context import strip, title_of

NAME = "Policy clarity"
CANDIDATES = {
    "returns": ["/policies/refund-policy", "/refund-policy", "/refund_returns", "/shipping-returns", "/pages/returns", "/returns", "/pages/return-policy", "/return-policy"],
    "shipping": ["/policies/shipping-policy", "/shipping-policy", "/delivery", "/shipping-returns", "/pages/shipping", "/shipping", "/pages/shipping-policy"],
    "contact": ["/pages/contact", "/policies/contact-information", "/contact", "/pages/contact-us", "/contact-us"],
}
LINK_RE = re.compile(r'href=["\']([^"\'#]+)["\']', re.I)
WORDS = {"returns": r"return|refund|exchange", "shipping": r"shipping|delivery|postage", "contact": r"contact|about"}
# words the page itself must contain to count as that policy (link words above only pick candidates)
PAGE_WORDS = {"returns": r"\b(returns?|refunds?|exchanges?)\b", "shipping": r"\b(shipping|delivery|postage|dispatch)\b",
              "contact": r"\b(contact|e-?mail|phone|call us|support)\b|@"}
NOT_FOUND_RE = re.compile(r"page not found|\b404\b|can.t find (that|this|the) page|page (you|you're) looking for", re.I)


def policy_text(ctx, path, kind, r):
    """Visible text if `r` looks like a real `kind` policy page, else None.
    Rejects soft 404s (redirect to home, 'page not found' title/heading) and pages that never mention the topic."""
    if not r.ok:
        return None
    final = urllib.parse.urlsplit(r.url).path or "/"
    if final == "/" and path.split("?")[0] not in ("", "/"):
        return None  # redirected to the home page
    text, title = strip(r.text), title_of(r.text)
    if NOT_FOUND_RE.search(title) or NOT_FOUND_RE.search(text[:300]):
        return None
    if len(text) <= 200 or not re.search(PAGE_WORDS[kind], title + " " + text, re.I):
        return None
    return text


def find(ctx, kind, home_links):
    linked = [l for l in dict.fromkeys(home_links) if re.search(WORDS[kind], l, re.I)][:4]
    paths = linked + [p for p in CANDIDATES[kind] if p not in linked]
    for p in paths:
        txt = policy_text(ctx, p, kind, ctx.get(p))
        if txt is not None:
            return p, txt
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
