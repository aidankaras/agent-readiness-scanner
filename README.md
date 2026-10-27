# agent-readiness-scanner

[![tests](https://github.com/aidankaras/agent-readiness-scanner/actions/workflows/test.yml/badge.svg)](https://github.com/aidankaras/agent-readiness-scanner/actions/workflows/test.yml)
![python](https://img.shields.io/badge/python-3.10%2B-blue) ![deps](https://img.shields.io/badge/dependencies-none-brightgreen) ![license](https://img.shields.io/badge/license-MIT-lightgrey)

Scores how ready an online store is for AI shopping agents (Google Universal Cart / AI Mode, ChatGPT shopping, agents using the Universal Commerce Protocol), 0-100, with evidence and a fix for every failed check.

**Why:** AI agents started browsing and checking out on shoppers' behalf in 2026. Store owners had no external way to see what those agents can read. Every check here is grounded in vendor documentation (Google, Shopify, OpenAI, ucp.dev), with sources and confidence labels in [docs/CHECKS.md](docs/CHECKS.md).

**First study:** 75 small stores. Shopify median 85, Wix/Squarespace/WooCommerce median 45; missing alt text and GTINs everywhere. [Read the findings](docs/FINDINGS-2026-10.md).

## Quick start

Python 3.10+, no third-party dependencies.

```bash
git clone https://github.com/aidankaras/agent-readiness-scanner
cd agent-readiness-scanner
pip install -e ".[dev]"

ars example-store.com --md            # markdown report
ars a.com b.com --csv out.csv         # JSON per store + summary CSV
pytest                                # offline fixture tests
```

## Example output

Report for the bundled test store (`tests/fixtures/good`), abridged:

```text
# Agent-readiness report: https://good.test
**Score: 85.0/100** (scanner v0.3.0, 2026-10-27T00:00:00Z; weights are provisional)
## PASS Page data quality (JSON-LD, crawler fallback) (weight 15)
- https://good.test/products/wool-runner: Product JSON-LD, missing none
## PASS Catalog / endpoint access (weight 10)
- sitemap.xml: 1 product URLs
- UCP endpoint https://good.test/api/ucp/mcp declared; GET probe HTTP 200 (host answers; protocol not exercised)
## PARTIAL Content completeness (weight 30)
- https://good.test/products/wool-runner: missing ['image alt text']
Fix: Fill in: image alt text. OpenAI feeds require title, description, url, brand, seller, image, price, availability; GTIN/MPN strongly recommended.
## PASS Policy clarity (weight 20)
- returns: /pages/returns
- shipping: /pages/shipping
- contact: /pages/contact
- return window stated: yes
## PASS Agent access (weight 10)
- robots.txt HTTP 200; shopping/search agents blocked on product page: none
- info: training crawlers blocked (not scored): none
- agent discovery files: ['/llms.txt'] (bonus only)
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

## How it crawls

- Identifies itself (`agent-readiness-scanner/0.3`) and obeys robots.txt for its own user agent.
- One request per second, at most 3 product pages per store, no login-gated pages, no checkout actions.
- The UCP endpoint is only probed with a GET; the protocol itself is not exercised.

## Limits

- Product and policy page discovery is heuristic; a "not found" can be a scanner miss.
- A single scan is a snapshot.
- It measures documented signals, not whether agents actually recommend or sell a store's products.

MIT licensed.
