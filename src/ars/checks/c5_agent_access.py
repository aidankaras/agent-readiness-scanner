import urllib.robotparser
from . import result

NAME = "Agent access"
# robots.txt tokens verified at vendor docs 2026-10-23 (see CHECKS.md "Crawler tokens").
# Scored: bots that surface/shop on behalf of users. Blocking these hides the store from AI answers.
AGENT_UAS = ["OAI-SearchBot", "ChatGPT-User", "Googlebot", "Storebot-Google", "PerplexityBot",
             "Perplexity-User", "Claude-SearchBot", "Claude-User", "Applebot"]
# Info only: model-training opt-outs. Blocking these is a legitimate owner choice, not a readiness defect.
TRAINING_UAS = ["GPTBot", "Google-Extended", "ClaudeBot", "Applebot-Extended"]
WALL_MARKERS = ["botfailover", "cf-challenge", "challenge-platform", "captcha", "px-captcha", "Access Denied"]


def check(ctx):
    ev = []
    pages = ctx.product_urls()
    target = pages[0] if pages else ctx.base + "/"
    rob = ctx.get("/robots.txt")
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(rob.text.splitlines() if rob.ok else [])
    blocked = [ua for ua in AGENT_UAS if not rp.can_fetch(ua, target)]
    ev.append(f"robots.txt HTTP {rob.status}; shopping/search agents blocked on product page: {blocked or 'none'}")
    tr = [ua for ua in TRAINING_UAS if not rp.can_fetch(ua, target)]
    ev.append(f"info: training crawlers blocked (not scored): {tr or 'none'}")
    wall = False
    for url in pages[:2]:
        r = ctx.f.get(url)
        challenged = r.ok and len(r.text) < 30000 and any(m.lower() in r.text.lower() for m in WALL_MARKERS)
        if r.status in (403, 429, 503) or challenged:
            wall = True
            ev.append(f"bot wall suspected on {url}: HTTP {r.status}")
    if not pages:
        sm = ctx.get("/sitemap.xml")
        if sm.ok and any(m.lower() in sm.text[:5000].lower() for m in WALL_MARKERS):
            wall = True
            ev.append("bot wall suspected: /sitemap.xml returned a challenge/failover page to the scanner")
    bonus = []
    for p in ("/agents.md", "/llms.txt"):
        r = ctx.get(p)
        if r.ok and "<html" not in r.text[:500].lower():
            bonus.append(p)
    ev.append(f"agent discovery files: {bonus or 'none'} (bonus only)")
    if wall or len(blocked) >= len(AGENT_UAS) // 2:
        st = "fail"
    elif blocked:
        st = "partial"
    else:
        st = "pass"
    return result("c5", NAME, st, ev, "Allow AI shopping agents in robots.txt and avoid bot challenges on product pages. Optional: publish /agents.md or /llms.txt.")
