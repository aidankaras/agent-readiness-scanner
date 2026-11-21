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
