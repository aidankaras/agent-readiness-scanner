# Agent-readiness report: https://bad.test

**Score: 5.0/100** (scanner v0.3.0, 2026-10-27T00:00:00Z; weights are provisional)

## FAIL Page data quality (JSON-LD, crawler fallback) (weight 15)
- https://bad.test/products/thing: no Product JSON-LD

Fix: Add schema.org Product + Offer JSON-LD with name, image, brand, price, priceCurrency, availability.

## PARTIAL Catalog / endpoint access (weight 10)
- sitemap.xml: 1 product URLs
- no UCP endpoint declared

Fix: Publish product URLs in sitemap.xml and expose a reachable UCP endpoint (Shopify does this automatically for eligible stores).

## FAIL Content completeness (weight 30)
- https://bad.test/products/thing: missing ['title 1-150 chars', 'description >=150 chars', 'image', 'image alt text', 'brand', 'price', 'availability', 'GTIN or MPN']

Fix: Fill in: GTIN or MPN, availability, brand, description >=150 chars, image, image alt text, price, title 1-150 chars. OpenAI feeds require title, description, url, brand, seller, image, price, availability; GTIN/MPN strongly recommended.

## FAIL Policy clarity (weight 20)
- returns: not found
- shipping: not found
- contact: not found
- return window stated: no

Fix: Publish reachable returns (with window in days and cost), shipping, and contact pages; Google requires return window/cost/link and a support contact for agentic checkout.

## FAIL Agent access (weight 10)
- robots.txt HTTP 200; shopping/search agents blocked on product page: ['OAI-SearchBot', 'ChatGPT-User', 'PerplexityBot', 'Claude-SearchBot', 'Claude-User']
- info: training crawlers blocked (not scored): ['GPTBot', 'Google-Extended', 'ClaudeBot']
- agent discovery files: none (bonus only)

Fix: Allow AI shopping agents in robots.txt and avoid bot challenges on product pages. Optional: publish /agents.md or /llms.txt.

## FAIL Checkout signals (UCP profile) (weight 15)
- /.well-known/ucp: HTTP 404

Fix: Publish a UCP profile at /.well-known/ucp (automatic on eligible Shopify stores; otherwise via Google's UCP integration).

## INFO Checkout-ineligible flags (informational)
- https://bad.test/products/thing: final sale
- https://bad.test/products/thing: pre-order

Fix: Google marks subscriptions, final-sale and pre-order items ineligible for agentic checkout; flag them in Merchant Center.
