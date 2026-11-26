# agent-readiness-scanner

[![tests](https://github.com/aidankaras/agent-readiness-scanner/actions/workflows/test.yml/badge.svg)](https://github.com/aidankaras/agent-readiness-scanner/actions/workflows/test.yml)
![python](https://img.shields.io/badge/python-3.10%2B-blue) ![deps](https://img.shields.io/badge/dependencies-none-brightgreen) ![license](https://img.shields.io/badge/license-MIT-lightgrey)

**Status: archived November 2026.** No longer maintained; issues and pull requests are closed.

Scores how ready an online store is for AI shopping agents (Google Universal Cart / AI Mode, ChatGPT shopping, agents using the Universal Commerce Protocol), 0-100, with evidence and a fix for every failed check.

**Why:** AI agents started browsing and checking out on shoppers' behalf in 2026. Store owners had no external way to see what those agents can read. Most checks are grounded in vendor documentation (Google, Shopify, OpenAI, ucp.dev), with sources and confidence labels in [docs/CHECKS.md](docs/CHECKS.md). Two parts are assumptions: check 1 (no vendor doc says agents read on-page JSON-LD) and the 150-character minimum description length.

**Store study, re-run November 2026 with scanner v0.4.0:** the same store list as October, 74 stores still reachable and in scope. Shopify median 80, Wix/Squarespace/WooCommerce median 45; image alt text missing on 47% of product pages, no GTIN or MPN on 61%. The Shopify figure would be 85 if a declared UCP endpoint answering GET with 404 counted as reachable, as it did in v0.3.0; the re-run explains why that is uncertain. [Read the re-run](docs/FINDINGS-2026-11-rerun.md).

**Correction to the first study (October 2026, scanner v0.3.0):** its alt-text figure (missing on 66% of pages) came from a scanner bug: v0.3.0 could only read alt text on Shopify, so every non-Shopify page counted as missing. Fixed in v0.4.0. The re-run above measures it properly and separates scanner fixes from store changes over the month. The [original findings](docs/FINDINGS-2026-10.md) stay as published, with a correction note at the top.

## Quick start

Python 3.10+, no third-party dependencies.

```bash
git clone https://github.com/aidankaras/agent-readiness-scanner
cd agent-readiness-scanner
pip install -e ".[dev]"

ars example.com --md                  # markdown report (use a store you own or may scan)
ars a.com b.com --csv out.csv         # JSON per store + summary CSV
pytest                                # offline fixture tests
```

## Example output

Report for the bundled test store (`tests/fixtures/good`), abridged. Full reports for a good and a bad fixture store, as markdown and JSON, are in [examples/](examples/) (a test keeps them in sync with the code):

```text
# Agent-readiness report: https://good.test
**Score: 100.0/100** (scanner v0.4.0, 2026-10-27T00:00:00Z; weights are provisional)
## PASS Page data quality (JSON-LD, crawler fallback) (weight 15)
- https://good.test/products/wool-runner: Product JSON-LD, missing none
## PASS Catalog / endpoint access (weight 10)
- sitemap.xml: 1 product URLs
- UCP endpoint https://good.test/api/ucp/mcp declared; GET probe HTTP 200 (answers; protocol not exercised)
## PASS Content completeness (weight 30)
- https://good.test/products/wool-runner: missing none
## PASS Policy clarity (weight 20)
- returns: /pages/returns
- shipping: /pages/shipping
- contact: /pages/contact
- return window stated: yes
## PASS Agent access (weight 10)
- robots.txt HTTP 200; shopping/search agents blocked on product page: none
- info: training crawlers blocked (not scored): none
- info: agent discovery files (not scored): ['/llms.txt']
## PASS Checkout signals (UCP profile) (weight 15)
- ucp.version 2026-08-25
- services ['dev.ucp.shopping']
- capabilities ['dev.ucp.shopping.checkout']
## INFO Checkout-ineligible flags (informational)
- none detected
```

## Design

```text
src/ars/
  fetch.py      polite HTTP client (robots.txt, rate limit, per-run cache) + fixture fetcher for tests
  context.py    per-scan state: product URL discovery (sitemap, Shopify, WooCommerce Store API, links), JSON-LD parsing
  checks/       one module per check, each returns {status, evidence, fix}
  score.py      weighted score; a crashing check is recorded as a failure, never kills the scan
  report.py     markdown and CSV output
```

Decisions worth noting:
- **Evidence over verdicts.** Every status carries the URLs and fields that produced it, so a score can be audited by hand.
- **Deterministic and offline-testable.** Network access sits behind one interface; tests run against fixture stores with no network.
- **Weights changed with data.** v0.2 weights were set from the docs; after the first sample showed every Shopify store passing platform-level checks by default, v0.3 shifted weight to the content merchants actually control.

## What it checks

| # | Check | Weight |
|---|-------|-------:|
| 1 | Product structured data on the page (schema.org JSON-LD) | 15 |
| 2 | Catalog discoverable (sitemap product URLs, declared UCP endpoint) | 10 |
| 3 | Product content: title, description, images + alt text, brand, price, availability, GTIN/MPN, variants | 30 |
| 4 | Return, shipping and contact policies; return window stated | 20 |
| 5 | AI search/shopping bots allowed (robots.txt, bot walls); training-bot blocks shown but not scored | 10 |
| 6 | UCP profile at `/.well-known/ucp` with checkout/cart capability | 15 |
| - | Checkout-ineligible items (final sale, pre-order, subscribe & save), informational | - |

Weights are provisional; see [docs/SPEC.md](docs/SPEC.md).

## Tests

`pytest` runs offline against fixture stores in `tests/fixtures` (good, bad, Shopify, bot-wall, training-bot-block) and small stores built inside the tests. It covers scoring weights, determinism, report output, the pass, partial and fail result of each scored check, the Shopify, WooCommerce and home-page-link product discovery paths, and the HTTP client's robots.txt, error, cache and rate-limit handling (with the network faked). Nothing hits the network. The Shopify fixture follows the fields the scanner reads; it has not been compared with a live store's JSON.

## How it crawls

- Identifies itself (`agent-readiness-scanner/0.4`) and obeys robots.txt for its own user agent.
- One request per second, at most 3 product pages per store, no login-gated pages, no checkout actions.
- The UCP endpoint is only probed with a GET; the protocol itself is not exercised.

## Limits

- Product and policy page discovery is heuristic; a "not found" can be a scanner miss. Product URLs are matched by path pattern (for example `/products/<slug>` or `/p/<slug>`), and home-page links with `?` or `#` are skipped.
- Alt text off Shopify is read from `<img>` tags in the page HTML. Images added by JavaScript after load are not seen, so their alt text counts as missing.
- On Shopify, availability comes from JSON-LD, with a fallback to an `available` field on product-JSON variants. Whether `/products/<handle>.json` includes that field has not been checked against a live store.
- robots.txt is checked for the requested URL, not again after a redirect. Python's `robotparser` ignores `*` and `$` wildcards in paths, so wildcard rules can be missed (in check 5 too). Response bodies are cut at 3 MB, which can make a very large JSON response look invalid.
- A declared UCP endpoint that answers the GET probe with 404 is rated "path not found". An MCP endpoint that only routes POST can answer a GET that way, so this can be a false negative; in the November re-run every Shopify store's endpoint did.
- A single scan is a snapshot.
- The store study's store list and raw data are not included in this repo; both findings docs report aggregates only and can't be reproduced from here. The October study used v0.3.0 (see its correction note); the November re-run used v0.4.0.
- Weights are hand-set, not fitted.
- It measures documented signals, not whether agents actually recommend or sell a store's products.

## Roadmap

- Publish the study's store list and per-store results so the findings are reproducible.
- Fit weights against an outcome measure once any public data on agent behavior exists.
- Exercise the UCP protocol (not just GET the profile) behind an explicit flag.
- Better policy-page discovery; fewer false "not found".

MIT licensed.
