# Spec v0.1 (draft, scoring weights are hypotheses to calibrate on the 50-store sample)

## Input
URL of a public store (Shopify first; generic sites best-effort).

## Checks (each returns pass/partial/fail + evidence + fix text)
Revised after M0 (see docs/CHECKS.md). Weights remain placeholders until the M2 sample.
1. Page data quality (crawler fallback): schema.org Product/Offer JSON-LD on product pages; price, currency, availability, brand, image. M0: no vendor doc says agents read page JSON-LD, so weight is reduced (15)
2. Catalog/endpoint access: sitemap.xml with product URLs; /api/ucp/mcp or UCP-declared endpoint reachable; /products.json is informational only (15)
3. Content completeness (maps to OpenAI required fields + Shopify Catalog attrs): title <=150 chars, description >=150 chars and plain text, image, brand, price, availability, GTIN or MPN+brand, variants labeled, image alt text (20)
4. Policy clarity: shipping/returns/contact reachable and parseable; return window, cost, and policy link present (Google requires these) (15)
5. Agent access: robots.txt does not blanket-block known agent UAs (advisory only); /agents.md or /llms.txt present (bonus, Shopify default); no bot-wall on product pages (15)
6. Checkout signals: /.well-known/ucp returns JSON, parses, lists dev.ucp.shopping.checkout and/or cart, endpoint reachable (20). x402 dropped from v0.1 (no primary source)
Informational (unscored): checkout-ineligible product flags (subscription, final-sale, pre-order).
Score = weighted sum, 0-100.

## Output
- JSON: {url, score, checks:[{id,status,evidence,fix}], scanned_at, version}
- Markdown report (1 page) rendered from JSON for owners.
- Aggregate CSV across stores for the data study.

## Non-goals (v0.1)
No auto-fixing, no login-gated pages, no price scraping at scale, no UI, no hosted service.

## Layout
src/ scanner modules (fetch.py, checks/*.py, score.py, report.py), tests/ with saved HTML fixtures, docs/, data/ (gitignored), README.

## Acceptance
- pytest passes on fixtures for each check.
- Scanner runs end-to-end on 5 real stores and output is sanity-reviewed by hand.
- Re-running the same store gives identical score (deterministic).
