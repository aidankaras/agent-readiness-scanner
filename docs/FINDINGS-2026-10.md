# Your store platform has already decided most of your AI-shopping readiness

> **Correction (November 2026).** The scanner version used for this study (v0.3.0) could only read image alt text from Shopify's product JSON. Every non-Shopify product page was counted as missing alt text, whatever the page actually had. So:
> - The figure "Image alt text missing on 144 of 219 pages (66%)" is wrong. All 63 non-Shopify pages were counted as missing, so the alt-text rate was not measured off Shopify. On the 156 Shopify pages, alt text was missing on at most 81 (52%).
> - Off Shopify, the content-completeness check could reach "partial" at best (15 of its 30 points), so the non-Shopify medians below (45, 62.5, 45, 42.5) may be understated.
> - The policy check in v0.3.0 also accepted some soft-404 and script-only pages as policy pages, and the catalog check counted a declared UCP endpoint answering 404 as reachable. The policy counts (13 of 23, 3 of 52) and the catalog result could move in either direction.
>
> These are fixed in scanner v0.4.0. The store list and raw results are not in this repo, so the numbers below have not been re-run; they are left as originally published, apart from the struck-through alt-text line.

AI shopping is live. Google's Universal Cart launched in the U.S. on October 15, 2026 in Search and the Gemini app. ChatGPT surfaces products from merchant feeds. Behind both sits a new open standard, the Universal Commerce Protocol (UCP): a store publishes a small file at `/.well-known/ucp` that tells AI agents how to browse and buy.

I wanted to know how ready small online stores are. So I built a scanner that checks what the vendors' own documentation says agents use, and ran it on 75 small stores in October 2026.

## What I checked
Six checks, grounded in Google, Shopify and OpenAI developer docs:
1. Structured product data on the page (schema.org JSON-LD)
2. Whether agents can find the catalog (sitemap, UCP endpoint)
3. Product content: title, description, images with alt text, brand, price, availability, GTIN/MPN
4. Return, shipping and contact policies (Google requires return terms for agentic checkout)
5. Whether AI search and shopping bots are allowed in robots.txt
6. Whether the store publishes a UCP profile

## Results
- **52 small Shopify stores: median 85/100.** Every one publishes a UCP profile, exposes its catalog, and lets AI agents in. Shopify does this by default.
- **23 small non-Shopify stores: median 45/100.**
  - Wix (6): median 62.5. All six publish a UCP profile.
  - Squarespace (7): median 45. None publish one.
  - WooCommerce (10): median 42.5. One publishes a UCP profile that is incomplete or doesn't parse; none publish a complete one.

The platform choice explained most of the gap. A WooCommerce or Squarespace merchant can't fix the biggest item by editing products: the checkout protocol has to come from the platform or a plugin.

## The gap everyone shares: content
Across 219 product pages I checked:
- ~~**Image alt text missing on 144** (66%)~~ See the correction above: on the 156 Shopify pages, alt text was missing on at most 81 (52%); non-Shopify pages were not measured.
- **No GTIN or MPN on 136** (62%). OpenAI's product feed spec lists these identifiers; agents use them to match products.
- On non-Shopify stores, **brand missing on 29 of 63** pages.
- **13 of 23** non-Shopify stores had no findable return or shipping policy, versus 3 of 52 on Shopify.

No platform fills these in for you. They are the part a merchant controls.

## What to do
- **On Shopify or Wix:** your protocol plumbing is done. Spend the time on alt text, GTINs and a clear return policy with a stated window.
- **On WooCommerce or Squarespace:** check whether your platform or a plugin offers UCP or Google's agentic checkout, and fix the content gaps above.
- **Everyone:** don't block AI search bots (OAI-SearchBot, Storebot-Google, PerplexityBot) in robots.txt unless you mean to. Blocking training bots like GPTBot is a separate choice and doesn't hide you from shoppers.

## Method and limits
- Stores found by category web search (apparel, beauty, home, food; plus pottery, leather, tea, coffee for non-Shopify), not a random sample. 4 non-Shopify stores where the scanner couldn't locate products were excluded.
- One scan per store, 3 product pages each, October 2026. Polite crawler, robots.txt respected.
- Scores use provisional weights. Policy detection is heuristic and may miss pages.
- I measured signals vendors document. I did not measure whether agents actually recommend or sell these stores' products; no public data on that exists yet.
