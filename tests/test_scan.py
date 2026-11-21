import json, pathlib
from ars.fetch import FixtureFetcher
from ars.score import scan, WEIGHTS
from ars.report import markdown, csv_rows

FX = pathlib.Path(__file__).parent / "fixtures"


def run(name, root=FX):
    return scan(f"https://{name}.test", FixtureFetcher(f"https://{name}.test", root / name), now="2026-01-01T00:00:00Z")


def store(tmp_path, files, base="good", drop=(), name="tmp"):
    """Ad-hoc fixture store: copy of fixtures/<base>, minus `drop`, plus `files` (fixture key -> content).
    URLs inside the copied files are rewritten to https://<name>.test. Returns the scan result."""
    d = tmp_path / name
    d.mkdir()
    if base:
        for f in (FX / base).iterdir():
            if f.name not in drop:
                (d / f.name).write_text(f.read_text().replace(f"https://{base}.test", f"https://{name}.test"))
    for k, v in files.items():
        (d / k).write_text(v)
    return run(name, tmp_path)


def check(res, cid):
    return next(c for c in res["checks"] if c["id"] == cid)


def page(body="", ld=None):
    ld = ld if ld is not None else GOOD_LD
    return f'<html><head><script type="application/ld+json">{json.dumps(ld)}</script></head><body>{body}</body></html>'


GOOD_LD = {"@type": "Product", "name": "Wool Runner", "description": "Lightweight merino running shoe. " * 6,
           "image": "https://tmp.test/i.jpg", "brand": {"@type": "Brand", "name": "GoodCo"}, "gtin13": "0123456789012",
           "offers": {"@type": "Offer", "price": "98.00", "priceCurrency": "USD", "availability": "https://schema.org/InStock"}}


def st(res):
    return {c["id"]: c["status"] for c in res["checks"]}


def test_weights_sum_100():
    assert sum(WEIGHTS.values()) == 100


def test_good_store_all_pass():
    r = run("good")
    assert st(r) == {"c1": "pass", "c2": "pass", "c3": "pass", "c4": "pass", "c5": "pass", "c6": "pass", "c7": "info"}, r
    assert r["score"] == 100.0


def test_bad_store():
    r = run("bad")
    s = st(r)
    assert s["c1"] == "fail" and s["c6"] == "fail" and s["c5"] == "fail" and s["c4"] == "fail"
    assert s["c2"] == "partial"  # sitemap only
    c7 = next(c for c in r["checks"] if c["id"] == "c7")
    assert any("final sale" in e for e in c7["evidence"]) and any("pre-order" in e for e in c7["evidence"])
    assert r["score"] < 20


def test_deterministic():
    assert json.dumps(run("good")) == json.dumps(run("good"))


def test_report_and_csv():
    r = run("good")
    assert "Score: 100.0/100" in markdown(r)
    rows = list(csv_rows([r, run("bad")]))
    assert rows[0][:2] == ["url", "score"] and len(rows) == 3


def test_fail_fixes_present():
    for c in run("bad")["checks"]:
        if c["status"] in ("fail", "partial"):
            assert c["fix"]


def test_bot_wall_and_html_ucp():
    s = st(run("wall"))
    assert s["c5"] == "fail" and s["c6"] == "fail"


def test_training_block_not_penalized():
    r = run("trainblock")
    assert st(r)["c5"] == "pass"
    assert r["score"] == run("good")["score"]  # training-bot blocks cost nothing
    c5 = next(c for c in r["checks"] if c["id"] == "c5")
    assert any("GPTBot" in e for e in c5["evidence"])


def test_partial_agent_block():
    import ars.checks.c5_agent_access as m
    assert "Storebot-Google" in m.AGENT_UAS and "GPTBot" not in m.AGENT_UAS


def test_product_url_patterns():
    from ars.context import PROD_RE
    for u in ["https://x.com/products/a","https://x.com/product/a/","https://x.com/shop/p/a","https://x.com/product-page/a"]:
        assert PROD_RE.search(u), u
    assert not PROD_RE.search("https://x.com/pages/about")


def test_examples_match_code():
    root = pathlib.Path(__file__).parents[1] / "examples"
    for name in ("good", "bad"):
        res = scan(f"https://{name}.test", FixtureFetcher(f"https://{name}.test", FX / name), now="2026-10-27T00:00:00Z")
        assert (root / f"{name}-store.md").read_text() == markdown(res)
        assert json.loads((root / f"{name}-store.json").read_text()) == res


# --- c3 content completeness, non-Shopify alt text (read from <img> tags) ---

def test_c3_non_shopify_can_pass_with_img_alt(tmp_path):
    r = store(tmp_path, {"products__wool-runner": page('<img src="https://tmp.test/i.jpg?width=600" alt="A nice shoe">')})
    assert check(r, "c3")["status"] == "pass", check(r, "c3")


def test_c3_img_without_alt_is_missing(tmp_path):
    r = store(tmp_path, {"products__wool-runner": page('<img src="https://tmp.test/i.jpg" alt="">')})
    c = check(r, "c3")
    assert c["status"] == "partial" and "image alt text" in c["evidence"][0]


def test_c3_no_img_tag_counts_alt_missing(tmp_path):
    # JSON-LD image but no <img> in the HTML (e.g. JS-rendered): alt text can't be seen, so it isn't credited
    r = store(tmp_path, {"products__wool-runner": page("Wool Runner")})
    assert "image alt text" in check(r, "c3")["evidence"][0]


def test_c3_prefers_product_image_over_decorative_imgs(tmp_path):
    body = '<img src="/logo.svg" alt="GoodCo"><img src="/icon.svg" alt="cart"><img src="https://cdn.tmp.test/files/i.jpg?v=1">'
    r = store(tmp_path, {"products__wool-runner": page(body)})
    assert "image alt text" in check(r, "c3")["evidence"][0]  # the product image itself has no alt


def test_img_tag_parsing():
    from ars.checks.c3_completeness import img_tags, html_alt_counts
    tags = img_tags("<IMG src='a.jpg' ALT=\"x &amp; y\"><img data-src=b.jpg>")
    assert tags == [{"src": "a.jpg", "alt": "x & y"}, {"data-src": "b.jpg"}]
    assert html_alt_counts("<img src=a.jpg alt=x><img src=b.jpg>", []) == (2, 1)
    assert html_alt_counts("<p>no images</p>", ["https://x/a.jpg"]) == (0, 0)


# --- c4 policy pages: soft 404s, JS shells, keyword match ---

class AlwaysFetcher:
    """Answers every URL with the same 200 HTML body; `final` (path) simulates a redirect."""

    def __init__(self, body, final=None):
        self.body, self.final = body, final

    def get(self, url):
        from ars.fetch import Resp
        import urllib.parse
        u = urllib.parse.urlsplit(url)
        return Resp(f"{u.scheme}://{u.netloc}{self.final}" if self.final else url, 200, "text/html", self.body)


def c4_of(fetcher):
    return check(scan("https://spa.test", fetcher, now="2026-01-01T00:00:00Z"), "c4")


def test_c4_js_shell_is_not_a_policy_page():
    script = "window.__STATE__ = " + json.dumps({"copy": "Free shipping. 30-day returns. Contact support. " * 20})
    shell = f"<html><head><title>Shop</title><script>{script}</script><style>body{{margin:0}}</style></head><body><div id=app></div></body></html>"
    c = c4_of(AlwaysFetcher(shell))
    assert c["status"] == "fail", c
    assert "return window stated: no" in c["evidence"]


def test_c4_soft_404_is_not_a_policy_page():
    body = "<html><head><title>Page not found</title></head><body><h1>Page not found</h1>" + "<p>Browse our latest collections and new arrivals.</p>" * 8 + "<footer>Free shipping and 30-day returns. Contact us.</footer></body></html>"
    assert c4_of(AlwaysFetcher(body))["status"] == "fail"


def test_c4_redirect_to_home_is_not_a_policy_page():
    body = "<html><body>" + "<p>Returns, shipping and contact information for our shop, 30 days.</p>" * 6 + "</body></html>"
    assert c4_of(AlwaysFetcher(body, final="/"))["status"] == "fail"


def test_c4_page_must_mention_its_topic(tmp_path):
    about = "<p>" + "We are a small family business making shoes by hand in Maine. " * 6 + "</p>"
    r = store(tmp_path, {"pages__returns": about}, drop=("pages__shipping",))
    c = check(r, "c4")
    assert "returns: not found" in c["evidence"] and "shipping: not found" in c["evidence"]
    assert c["status"] == "fail"  # contact only: 1 of 4 points


def test_c4_partial_policy_without_window(tmp_path):
    ret = "<p>" + "Unworn items can be returned for a refund or exchange; email us to start a return. " * 4 + "</p>"
    r = store(tmp_path, {"pages__returns": ret})
    c = check(r, "c4")
    assert c["status"] == "partial" and "return window stated: no" in c["evidence"], c


# --- c2 catalog / endpoint access ---

class StatusFetcher(FixtureFetcher):
    """FixtureFetcher that answers chosen paths with a fixed status code."""

    def __init__(self, base, root, statuses):
        super().__init__(base, root)
        self.statuses = statuses

    def get(self, url):
        from ars.fetch import Resp
        import urllib.parse
        path = urllib.parse.urlsplit(url).path
        if path in self.statuses:
            return Resp(url, self.statuses[path], "text/html", "")
        return super().get(url)


def c2_with_endpoint_status(code):
    f = StatusFetcher("https://good.test", FX / "good", {"/api/ucp/mcp": code})
    return check(scan("https://good.test", f, now="2026-01-01T00:00:00Z"), "c2")


def test_c2_declared_endpoint_404_is_not_reachable():
    for code in (404, 410):
        c = c2_with_endpoint_status(code)
        assert c["status"] == "partial", c  # sitemap only
        assert "path not found" in c["evidence"][1]


def test_c2_post_only_endpoint_still_answers():
    for code in (405, 401, 403, 400):
        assert c2_with_endpoint_status(code)["status"] == "pass", code


def test_c2_endpoint_down():
    c = c2_with_endpoint_status(503)
    assert c["status"] == "partial" and "unreachable" in c["evidence"][1]


def test_c2_fail_and_sitemap_evidence(tmp_path):
    r = store(tmp_path, {}, drop=("sitemap.xml", ".well-known__ucp"))
    c = check(r, "c2")
    assert c["status"] == "fail" and c["evidence"][0] == "sitemap.xml: HTTP 404 (not available)", c
    r2 = store(tmp_path, {"sitemap.xml": "<urlset><url><loc>https://tmp2.test/pages/about</loc></url></urlset>"}, name="tmp2")
    assert check(r2, "c2")["evidence"][0] == "sitemap.xml: HTTP 200, no product URLs"


# --- c6 checkout signals: UCP profile shapes ---

def ucp(obj):
    return {".well-known__ucp": json.dumps(obj)}


def test_c6_capabilities_and_services_as_lists(tmp_path):
    prof = {"ucp": {"version": "2026-08-25",
                    "services": [{"name": "dev.ucp.shopping", "transport": "mcp", "endpoint": "https://tmp.test/api/ucp/mcp"}],
                    "capabilities": [{"name": "dev.ucp.shopping.checkout", "version": "2026-08-25"}]}}
    r = store(tmp_path, ucp(prof))
    assert check(r, "c6")["status"] == "pass", check(r, "c6")
    assert check(r, "c2")["status"] == "pass"  # endpoint found in list-form services


def test_c6_partial_without_checkout_capability(tmp_path):
    prof = {"ucp": {"version": "2026-08-25", "services": {"dev.ucp.shopping": []}, "capabilities": {"dev.ucp.shopping.order": [{}]}}}
    c = check(store(tmp_path, ucp(prof)), "c6")
    assert c["status"] == "partial" and c["fix"]


def test_c6_partial_on_invalid_or_odd_profile(tmp_path):
    for i, body in enumerate(['{"ucp": ', '{"ucp": ["not", "a", "map"]}', '{"ucp": {"version": "x", "capabilities": "checkout"}}']):
        c = check(store(tmp_path, {".well-known__ucp": body}, name=f"odd{i}"), "c6")
        assert c["status"] == "partial", (body, c)
        assert not any("check error" in e for e in c["evidence"])


def test_crashing_check_is_recorded_not_raised(monkeypatch):
    import ars.score
    import ars.checks.c4_policy as c4

    def boom(ctx):
        raise RuntimeError("kaput")
    monkeypatch.setattr(ars.score, "ALL", [boom if fn.__module__ == c4.__name__ else fn for fn in ars.score.ALL])
    boom.__module__ = c4.__name__
    r = run("good")
    c = check(r, "c4")
    assert c["status"] == "fail" and c["name"] == c4.NAME and "RuntimeError: kaput" in c["evidence"][0]
    assert r["score"] == 80.0


# --- Shopify path: discovery via /products.json, content from /products/<handle>.json ---

def test_shopify_store():
    r = run("shopify")
    assert st(r) == {"c1": "partial", "c2": "partial", "c3": "partial", "c4": "pass", "c5": "pass", "c6": "pass", "c7": "info"}, r
    assert r["score"] == 72.5
    c2, c3 = check(r, "c2"), check(r, "c3")
    assert any("/products.json public" in e for e in c2["evidence"])
    # discovered through /products.json?limit=5 (no sitemap), in catalog order
    assert c3["evidence"] == ["https://shopify.test/products/linen-shirt: missing none",
                              "https://shopify.test/products/wool-hat: missing ['image alt text', 'GTIN or MPN']"]


def test_shopify_facts_from_product_json():
    from ars.checks.c3_completeness import gather
    from ars.context import Ctx
    ctx = Ctx("https://shopify.test", FixtureFetcher("https://shopify.test", FX / "shopify"))
    url, pg = ctx.product_pages()[1]
    d = gather(ctx, url, pg)
    assert d["title"] == "Wool Beanie" and d["brand"] == "Shopify Test Co" and len(d["desc"]) >= 150
    assert (d["images"], d["alts"], d["alt_of"]) == (1, 0, 1)
    assert d["price"] and not d["ident"] and d["variants_ok"]
    assert d["avail"]  # not in this page's JSON-LD; taken from the variant's "available" key


def test_shopify_unlabeled_variants(tmp_path):
    p = json.loads((FX / "shopify" / "products__linen-shirt.json").read_text())
    for v in p["product"]["variants"]:
        v["title"] = "Default Title"
    r = store(tmp_path, {"products__linen-shirt.json": json.dumps(p)}, base="shopify")
    assert "variants labeled" in check(r, "c3")["evidence"][0]


def test_shopify_sitemap_index_is_followed(tmp_path):
    files = {"sitemap.xml": "<sitemapindex><sitemap><loc>https://tmp.test/sitemap_products_1.xml</loc></sitemap></sitemapindex>",
             "sitemap_products_1.xml": "<urlset><url><loc>https://tmp.test/products/wool-hat</loc></url></urlset>"}
    r = store(tmp_path, files, base="shopify")
    assert check(r, "c2")["evidence"][0] == "sitemap.xml: 1 product URLs"
    assert check(r, "c3")["evidence"][0].startswith("https://tmp.test/products/wool-hat")
