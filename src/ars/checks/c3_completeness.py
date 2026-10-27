import re, html
from . import result
from ..context import ld_products, walk

NAME = "Content completeness"


def strip(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h or ""))).strip()


def gather(ctx, url, page):
    """Merge Shopify product JSON (if any) with JSON-LD. Returns dict of facts."""
    d = {"title": "", "desc": "", "images": 0, "alts": 0, "brand": "", "price": False, "avail": False, "ident": False, "variants_ok": True}
    sp = ctx.shopify_product_json(url) if ctx.is_shopify() else None
    if sp:
        d["title"] = sp.get("title") or ""
        d["desc"] = strip(sp.get("body_html"))
        imgs = sp.get("images") or []
        d["images"] = len(imgs); d["alts"] = sum(1 for i in imgs if (i.get("alt") or "").strip())
        d["brand"] = sp.get("vendor") or ""
        vs = sp.get("variants") or []
        d["price"] = any(v.get("price") for v in vs)
        d["ident"] = any((v.get("barcode") or "").strip() for v in vs)
        if len(vs) > 1:
            d["variants_ok"] = all((v.get("title") or "").strip() and v.get("title") != "Default Title" for v in vs)
    for p in ld_products(page.text if page.ok else ""):
        d["title"] = d["title"] or str(p.get("name") or "")
        d["desc"] = d["desc"] or strip(str(p.get("description") or ""))
        b = p.get("brand")
        d["brand"] = d["brand"] or (b.get("name", "") if isinstance(b, dict) else str(b or ""))
        if not d["images"] and p.get("image"):
            d["images"] = 1
        for o in walk(p):
            if any(o.get(k) for k in ("gtin", "gtin8", "gtin12", "gtin13", "gtin14", "mpn")):
                d["ident"] = True
            if o.get("price") or o.get("lowPrice"):
                d["price"] = True
            if o.get("availability"):
                d["avail"] = True
    if sp and not d["avail"]:
        d["avail"] = any("available" in v for v in (sp.get("variants") or []))
    return d


def score(d):
    items = {
        "title 1-150 chars": 0 < len(d["title"]) <= 150,
        "description >=150 chars": len(d["desc"]) >= 150,
        "image": d["images"] > 0,
        "image alt text": d["images"] > 0 and d["alts"] / max(d["images"], 1) >= 0.5,
        "brand": bool(d["brand"].strip()),
        "price": d["price"],
        "availability": d["avail"],
        "GTIN or MPN": d["ident"],
        "variants labeled": d["variants_ok"],
    }
    return items


def check(ctx):
    pages = ctx.product_pages()
    if not pages:
        return result("c3", NAME, "fail", ["no product pages discovered"], "Expose product URLs in sitemap.xml.")
    ev, fr, missing_all = [], [], set()
    for url, page in pages:
        items = score(gather(ctx, url, page))
        miss = [k for k, v in items.items() if not v]
        missing_all |= set(miss)
        fr.append(1 - len(miss) / len(items))
        ev.append(f"{url}: missing {miss or 'none'}")
    avg = sum(fr) / len(fr)
    st = "pass" if avg >= 0.89 else "partial" if avg >= 0.6 else "fail"
    return result("c3", NAME, st, ev, "Fill in: " + ", ".join(sorted(missing_all)) + ". OpenAI feeds require title, description, url, brand, seller, image, price, availability; GTIN/MPN strongly recommended.")
