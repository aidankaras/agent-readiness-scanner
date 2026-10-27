"""Shared per-scan state: base URL, fetcher, discovered product URLs, parsed product data."""
import json, re, urllib.parse
from .fetch import Fetcher

MAX_PRODUCTS = 3
LD_RE = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)
PROD_RE = re.compile(r"/(products?|product-page|p|shop/p|store/p)/[^/?#]+/?$", re.I)
LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)


def norm_base(url):
    if "://" not in url:
        url = "https://" + url
    p = urllib.parse.urlsplit(url)
    return f"{p.scheme}://{p.netloc}"


def jsonld_blocks(html):
    out = []
    for raw in LD_RE.findall(html or ""):
        try:
            out.append(json.loads(raw.strip()))
        except Exception:
            out.append({"__invalid__": True})
    return out


def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)


def types_of(d):
    t = d.get("@type", [])
    return set(t if isinstance(t, list) else [t])


def ld_products(html):
    return [d for b in jsonld_blocks(html) for d in walk(b) if types_of(d) & {"Product", "ProductGroup"}]


class Ctx:
    def __init__(self, url, fetcher=None):
        self.base = norm_base(url)
        self.f = fetcher or Fetcher()
        self._products = None

    def get(self, path):
        return self.f.get(path if path.startswith("http") else self.base + path)

    def is_shopify(self):
        r = self.get("/products.json?limit=1")
        return r.ok and '"products"' in r.text

    def sitemap_product_urls(self):
        r = self.get("/sitemap.xml")
        if not r.ok:
            return [], None
        locs = LOC_RE.findall(r.text)
        subs = [u for u in locs if u.endswith(".xml") or "sitemap" in u]
        prod = [u for u in locs if PROD_RE.search(u)]
        if not prod:
            for s in [u for u in subs if re.search(r"product|store|shop", u, re.I)][:3] or subs[:2]:
                sr = self.f.get(s)
                if sr.ok:
                    prod += [u for u in LOC_RE.findall(sr.text) if PROD_RE.search(u)]
        return prod, r

    def product_urls(self):
        if self._products is None:
            urls, _ = self.sitemap_product_urls()
            if not urls and self.is_shopify():
                try:
                    data = json.loads(self.get("/products.json?limit=5").text)
                    urls = [f"{self.base}/products/{p['handle']}" for p in data.get("products", [])]
                except Exception:
                    urls = []
            if not urls:  # WooCommerce public Store API
                r = self.get("/wp-json/wc/store/v1/products?per_page=5")
                if r.ok:
                    try:
                        urls = [p["permalink"] for p in json.loads(r.text) if p.get("permalink")]
                    except Exception:
                        urls = []
            if not urls:  # generic: product links on home page and /shop
                for path in ("/", "/shop", "/store", "/shop-all"):
                    h = self.get(path)
                    if h.ok:
                        for l in re.findall(r'href=["\']([^"\'#?]+)["\']', h.text):
                            if l.startswith("/"):
                                l = self.base + l
                            if l.startswith(self.base) and PROD_RE.search(l):
                                urls.append(l)
                    if urls:
                        break
            # deterministic: sitemap order, first N unique
            seen, out = set(), []
            for u in urls:
                if u not in seen:
                    seen.add(u); out.append(u)
            self._products = out[:MAX_PRODUCTS]
        return self._products

    def product_pages(self):
        return [(u, self.f.get(u)) for u in self.product_urls()]

    def shopify_product_json(self, url):
        r = self.f.get(url.split("?")[0] + ".json")
        if r.ok:
            try:
                return json.loads(r.text).get("product")
            except Exception:
                return None
        return None
