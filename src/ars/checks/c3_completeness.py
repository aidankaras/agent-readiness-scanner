import re, html
from ._result import result
from ..context import ld_products, walk, strip

NAME = "Content completeness"
IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
ATTR_RE = re.compile(r"""([a-zA-Z-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+))""")


def img_tags(page_html):
    """Attributes of every <img> tag in the HTML, as dicts."""
    out = []
    for tag in IMG_RE.findall(page_html or ""):
        out.append({m.group(1).lower(): html.unescape(m.group(2) or m.group(3) or m.group(4) or "") for m in ATTR_RE.finditer(tag[4:])})
    return out


def ld_image_urls(p):
    imgs = p.get("image")
    out = []
    for i in imgs if isinstance(imgs, list) else [imgs]:
        u = (i.get("url") or i.get("contentUrl")) if isinstance(i, dict) else i
        if isinstance(u, str) and u:
            out.append(u)
    return out


def html_alt_counts(page_html, ld_urls):
    """(images, with_alt) from <img> tags. Prefers tags whose src matches a JSON-LD image file name;
    falls back to all <img> tags with a src. (0, 0) when the HTML has no <img> (e.g. JS-rendered)."""
    def fname(u):
        return u.split("?")[0].rstrip("/").rsplit("/", 1)[-1].lower()
    tags = [t for t in img_tags(page_html) if t.get("src") or t.get("data-src")]
    names = {fname(u) for u in ld_urls if fname(u)}
    matched = [t for t in tags if fname(t.get("src") or t.get("data-src")) in names]
    use = matched or tags
    return len(use), sum(1 for t in use if t.get("alt", "").strip())


def gather(ctx, url, page):
    """Merge Shopify product JSON (if any) with JSON-LD. Returns dict of facts."""
    d = {"title": "", "desc": "", "images": 0, "alts": 0, "alt_of": 0, "brand": "", "price": False, "avail": False, "ident": False, "variants_ok": True}
    sp = ctx.shopify_product_json(url) if ctx.is_shopify() else None
    if sp:
        d["title"] = sp.get("title") or ""
        d["desc"] = strip(sp.get("body_html"))
        imgs = sp.get("images") or []
        d["images"] = d["alt_of"] = len(imgs)
        d["alts"] = sum(1 for i in imgs if (i.get("alt") or "").strip())
        d["brand"] = sp.get("vendor") or ""
        vs = sp.get("variants") or []
        d["price"] = any(v.get("price") for v in vs)
        d["ident"] = any((v.get("barcode") or "").strip() for v in vs)
        if len(vs) > 1:
            d["variants_ok"] = all((v.get("title") or "").strip() and v.get("title") != "Default Title" for v in vs)
    ld_urls = []
    for p in ld_products(page.text if page.ok else ""):
        ld_urls += ld_image_urls(p)
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
    if not sp and page.ok:  # off Shopify, alt text can only be read from the page's <img> tags
        d["alt_of"], d["alts"] = html_alt_counts(page.text, ld_urls)
    if sp and not d["avail"]:
        d["avail"] = any("available" in v for v in (sp.get("variants") or []))
    return d


def score(d):
    items = {
        "title 1-150 chars": 0 < len(d["title"]) <= 150,
        "description >=150 chars": len(d["desc"]) >= 150,
        "image": d["images"] > 0,
        # alt text: share of observed product images (Shopify JSON, else page <img> tags) with non-empty alt
        "image alt text": d["images"] > 0 and d["alt_of"] > 0 and d["alts"] / d["alt_of"] >= 0.5,
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
