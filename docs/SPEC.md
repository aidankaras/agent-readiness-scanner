# Spec (v0.4; weights unchanged since v0.3 and still provisional)

## Input
URL of a public store (Shopify first; generic sites best-effort).

## Checks (each returns pass/partial/fail + evidence + fix text)
Revised after the initial doc review (docs/CHECKS.md) and recalibrated after the first sample: checks every Shopify store passes by default weigh less, merchant-controlled content weighs more. Weights remain provisional; the authoritative values are `WEIGHTS` in `src/ars/score.py`.
1. Page data quality (crawler fallback): schema.org Product/Offer JSON-LD on product pages; price, currency, availability, brand, image. The doc review found no vendor doc saying agents read page JSON-LD, so weight is reduced (15)
2. Catalog/endpoint access: sitemap.xml with product URLs; UCP-declared endpoint reachable (a GET answered with 2xx/400/401/403/405; 404/410 count as not found); /products.json is informational only (10)
3. Content completeness (maps to OpenAI required fields + Shopify Catalog attrs): title <=150 chars, description >=150 chars (a heuristic, not a vendor threshold), image, brand, price, availability, GTIN or MPN+brand, variants labeled, image alt text (from Shopify product JSON, otherwise the product page's <img> tags) (30)
4. Policy clarity: shipping/returns/contact pages reachable and on topic (soft 404s and script-only pages rejected); return window stated in days (20). Google also requires return cost and a policy link; those are not checked
5. Agent access: robots.txt does not blanket-block known agent UAs (advisory only); /agents.md or /llms.txt presence reported (informational, not scored; Shopify default); no bot-wall on product pages (10); training-bot blocks are shown but not scored
6. Checkout signals: /.well-known/ucp returns JSON, parses, lists dev.ucp.shopping.checkout and/or cart (capabilities and services may be maps or lists) (15). Endpoint reachability is scored in check 2. x402 dropped from v0.1 (no primary source)
Informational (unscored): checkout-ineligible product flags (subscription, final-sale, pre-order).
Score = weighted sum, 0-100.

## Output
- JSON: {url, score, checks:[{id,status,evidence,fix}], scanned_at, version}
- Markdown report (1 page) rendered from JSON for owners.
- Aggregate CSV across stores for the data study.

## Non-goals (v0.4)
No auto-fixing, no login-gated pages, no price scraping at scale, no UI, no hosted service.

## Layout
src/ scanner modules (fetch.py, checks/*.py, score.py, report.py), tests/ with saved HTML fixtures, docs/, README.

## Acceptance
- pytest passes on fixtures for each check.
- Scanner runs end-to-end on real stores and output is sanity-reviewed by hand.
- Re-running the same store gives identical score (deterministic).
