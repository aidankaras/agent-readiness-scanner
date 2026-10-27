import json, pathlib
from ars.fetch import FixtureFetcher
from ars.score import scan, WEIGHTS
from ars.report import markdown, csv_rows

FX = pathlib.Path(__file__).parent / "fixtures"


def run(name):
    return scan(f"https://{name}.test", FixtureFetcher(f"https://{name}.test", FX / name), now="2026-01-01T00:00:00Z")


def st(res):
    return {c["id"]: c["status"] for c in res["checks"]}


def test_weights_sum_100():
    assert sum(WEIGHTS.values()) == 100


def test_good_store_all_pass():
    r = run("good")
    assert st(r) == {"c1": "pass", "c2": "pass", "c3": "partial", "c4": "pass", "c5": "pass", "c6": "pass", "c7": "info"}, r
    assert r["score"] == 85.0


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
    assert "Score: 85.0/100" in markdown(r)
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
