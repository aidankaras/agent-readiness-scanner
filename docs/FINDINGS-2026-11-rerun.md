# Re-run of the October 2026 study with scanner v0.4.0 (November 2026)

The [October 2026 study](FINDINGS-2026-10.md) used scanner v0.3.0, which had bugs (see the correction at the top of that page). This page re-runs the same study with v0.4.0. The October page stays as published, for the record.

**Read the differences with care.** The re-run happened about a month later (26 November 2026, UTC), and stores change. A difference between October and November can come from the scanner fixes or from the stores themselves. To separate the two, the November pages were scored twice: once by v0.4.0, and once by the v0.3.0 checks run on the very same saved responses. So:

- **October v0.3.0 to November v0.3.0** = the stores changed (same scanner).
- **November v0.3.0 to November v0.4.0** = the scanner changed (same pages).

The October raw pages were not saved, so October itself can't be re-scored. The split above assumes the code behind the October run matches the v0.3.0 release. That fits the data: on the 52 Shopify stores, 46 got the same score from v0.3.0 in October and in November.

## What was re-run
- The same store lists as October: 52 small Shopify stores and 27 small non-Shopify stores (Wix, Squarespace, WooCommerce, one BigCommerce), in the same order.
- The same procedure: one scan per store, sequential, one request per second, at most 3 product pages per store, robots.txt respected for the scanner's own user agent. Stores with no product pages found were retried once, as in October. 1,758 HTTP requests in total.
- The same rule for the sample: non-Shopify stores where the scanner can't locate products are excluded. The same 4 stores were excluded as in October.
- **One store lost:** one WooCommerce store's domain no longer resolves (DNS failure, also on the retry). It is recorded as lost, not replaced. The non-Shopify sample is 22 stores instead of 23, and 60 non-Shopify product pages instead of 63.
- No Shopify store was lost. All 52 still answer and still have product pages.

## Results (v0.4.0, November 2026)
- **52 small Shopify stores: median 80/100.** Every one publishes a UCP profile, lists products in its sitemap, and lets AI search and shopping bots in. The 5-point drop from October is a scanner change, not a store change; see "The catalog check" below.
- **22 small non-Shopify stores: median 45/100.**
  - Wix (6): median 55. All six publish a UCP profile.
  - Squarespace (7): median 45. None publish one.
  - WooCommerce (9): median 42.5. One publishes a UCP profile that is incomplete or doesn't parse; none publish a complete one.

The platform gap holds: 80 against 45.

Across 216 product pages:
- **Image alt text missing on 102** (47%): 79 of 156 Shopify pages (51%) and 23 of 60 non-Shopify pages (38%). This is the figure the October study got wrong.
- **No GTIN or MPN on 131** (61%).
- On non-Shopify stores, **brand missing on 29 of 60** pages.
- **13 of 22** non-Shopify stores had no findable return or shipping policy, against 3 of 52 on Shopify.

## October against November, split into store changes and scanner changes

| | Oct, v0.3.0 | Nov, v0.3.0 (same pages as next column) | Nov, v0.4.0 |
|---|---:|---:|---:|
| Shopify stores / median | 52 / 85 | 52 / 85 | 52 / **80** |
| Non-Shopify stores / median | 23 / 45 | 22 / 45 | 22 / **45** |
| Wix median (6 stores) | 62.5 | 60 | **55** |
| Squarespace median (7) | 45 | 45 | **45** |
| WooCommerce median | 42.5 (10) | 42.5 (9) | **42.5** (9) |
| Product pages | 219 | 216 | 216 |
| Alt text missing, all pages | 144 (66%) | 145 (67%) | **102 (47%)** |
| ... on Shopify pages | 81 of 156 | 85 of 156 | **79 of 156** |
| ... on non-Shopify pages | 63 of 63 | 60 of 60 | **23 of 60** |
| No GTIN or MPN | 136 (62%) | 131 (61%) | **131 (61%)** |
| Brand missing, non-Shopify pages | 29 of 63 | 29 of 60 | **29 of 60** |
| No return or shipping policy found, non-Shopify | 13 of 23 | 13 of 22 | **13 of 22** |
| No return or shipping policy found, Shopify | 3 of 52 | 2 of 52 | **3 of 52** |
| Catalog check passed, Shopify | 52 of 52 | 52 of 52 | **0 of 52** (all partial) |
| Catalog check passed, non-Shopify | 7 of 23 | 7 of 22 | **1 of 22** |
| UCP profile, Wix / Squarespace / WooCommerce | 6 / 0 / 0 (+1 incomplete) | same | **same** |

What the split shows:
- **Alt text: almost all scanner.** On the same November pages, v0.3.0 counted every non-Shopify page as missing alt text (60 of 60); v0.4.0, which reads the page's `<img>` tags, finds 23 of 60. The stores barely moved (144 to 145 under the old scanner, with three fewer pages).
- **GTIN, brand, non-Shopify policies: no scanner effect.** v0.3.0 and v0.4.0 agree on the November pages. The small October-to-November moves (136 to 131 missing GTINs) come from the lost store's three pages and from stores changing products.
- **Policy check:** the soft-404 fix changed the status of 5 stores' policy check on the same pages, in both directions. Net effect on the headline counts: Shopify stores with no policy found went from 2 to 3; non-Shopify unchanged at 13.
- **Non-Shopify medians were not understated after all.** The October correction warned they might be. With alt text now measured, two non-Shopify stores moved up a step on content, but the catalog change below took points off others, and the median stayed at 45. The Wix median fell from 62.5 to 55: 2.5 points from the stores themselves, 5 from the catalog change.

## The catalog check: read the Shopify drop with care
All 52 Shopify stores, 6 Wix stores and the one BigCommerce store declare a UCP endpoint that answers the scanner's GET request with HTTP 404. v0.3.0 counted any answer as reachable. v0.4.0 treats a 404 as "path not found" and rates the catalog check partial instead of pass, which takes 5 points off each of these stores. That one change explains the whole Shopify drop from 85 to 80: re-rating it the v0.3.0 way gives a Shopify median of 85 and a Wix median of 60 on the November data.

The 404 may not mean the endpoint is missing. These are MCP endpoints, which take JSON-RPC over POST; an endpoint that only routes POST can answer a GET with 404. On all 52 Shopify stores, the 404 comes back as an HTML "page not found" page, not as a JSON error from an API. The scanner only sends GET (it does not exercise the protocol), so this re-run can't tell a missing endpoint from a POST-only one. Treat the Shopify 80 and the Wix 55 as lower bounds on this point, and 85 and 60 as what they would be if those endpoints work.

## Method and limits
- Same as the October study: stores were found by category web search, not a random sample; one scan per store, 3 product pages each; scores use provisional weights; policy and product discovery are heuristic and can miss pages.
- Alt text off Shopify is read from `<img>` tags in the page HTML. Images added by JavaScript after load are not seen and count as missing, so the non-Shopify alt-text figure can overstate what is missing.
- One store was lost and the stores themselves changed over the month, so October and November are not the same sample of pages. The split table above shows which changes come from where.
- The per-store results and the store list stay unpublished, as for the October study; this page reports aggregates only.
- I measured signals vendors document. I did not measure whether agents actually recommend or sell these stores' products.
