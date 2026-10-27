from . import result
from ..context import ld_products, walk

NAME = "Page data quality (JSON-LD, crawler fallback)"
FIELDS = ["name", "image", "brand", "price", "priceCurrency", "availability"]


def offer_fields(p):
    have = {k for k in ("name", "image", "brand") if p.get(k)}
    for o in walk(p.get("offers", {})):
        for k in ("price", "priceCurrency", "availability"):
            if o.get(k) not in (None, ""):
                have.add(k)
        if o.get("lowPrice"):
            have.add("price")
    for v in walk(p.get("hasVariant", [])):
        for o in walk(v.get("offers", {})):
            for k in ("price", "priceCurrency", "availability"):
                if o.get(k) not in (None, ""):
                    have.add(k)
    return have


def check(ctx):
    pages = ctx.product_pages()
    if not pages:
        return result("c1", NAME, "fail", ["no product pages discovered"], "Expose product URLs in sitemap.xml.")
    scores, ev = [], []
    for url, r in pages:
        if not r.ok:
            ev.append(f"{url}: HTTP {r.status}"); scores.append(0); continue
        prods = ld_products(r.text)
        if not prods:
            ev.append(f"{url}: no Product JSON-LD"); scores.append(0); continue
        have = set().union(*(offer_fields(p) for p in prods))
        missing = [k for k in FIELDS if k not in have]
        scores.append((len(FIELDS) - len(missing)) / len(FIELDS))
        ev.append(f"{url}: Product JSON-LD, missing {missing or 'none'}")
    avg = sum(scores) / len(scores)
    st = "pass" if avg >= 0.99 else "partial" if avg >= 0.5 else "fail"
    return result("c1", NAME, st, ev, "Add schema.org Product + Offer JSON-LD with name, image, brand, price, priceCurrency, availability.")
