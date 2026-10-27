# CHECKS.md — M0 findings (2026-10-18)

Purpose: what agents actually consume, verified at primary sources, so SPEC.md checks and weights rest on evidence. Every claim below carries a source. Labels: **[V]** = read at primary source today; **[L]** = observed live on a real store today (1 store, single-point evidence); **[U]** = not verified / gap.
Raw page copies: /opt/data/cache/web/ (developers.openai.com, developers.google.com, shopify.dev, help.shopify.com, ucp.dev; prunable cache, re-fetch if needed).

## 1. Platform claims, verified

- Google Universal Cart is live in the U.S. in Search + Gemini app — **[V]** Google blog "An intelligent new shopping cart", dated 2026-10-15 (blog.google/products-and-platforms/products/shopping/universal-cart-launch/). Announced at I/O 2026-05-19. Named merchants: Nike, Sephora, Target, Ulta, Walmart, Wayfair, "many Shopify merchants". Checkout = Google Pay in cart OR hand-off to merchant site.
- UCP is a real, versioned open spec — **[V]** ucp.dev (versions seen: 2026-01-23, 2026-04-08, 2026-08-25). Google dev guide: developers.google.com/merchant/ucp. Co-developed with Shopify, Etsy, Wayfair, Target, Walmart (Google dev blog "Under the Hood: UCP").
- Shopify agent syndication is live, **on by default for eligible stores** — **[V]** help.shopify.com/en/manual/online-sales-channels/agentic-storefronts. Channels: ChatGPT, Google AI Mode/Gemini, Copilot, Meta.
- OpenAI agentic commerce is live as ACP + product feeds — **[V]** developers.openai.com/commerce (guides/get-started, specs/file-upload/products). Today ChatGPT is described by Shopify as "discovery-focused"; users finish checkout on the merchant's own checkout (Shopify help, ChatGPT section). OpenAI checkout is "a separately enabled integration" (OpenAI products spec).

Conclusion: PLAN's "UNCONFIRMED" evidence is now confirmed at primary sources for Google, Shopify, OpenAI. Sources are vendor docs, so adoption/impact (how many shoppers, any sales lift) is **[U]**; do not claim it publicly.

## 2. What each ecosystem consumes

### 2a. Shopify (merchant-side, from help.shopify.com + shopify.dev) [V]
- Primary path is **Shopify Catalog** (Shopify-hosted syndication), not the storefront HTML. Fields passed: title, description, options, images, price, availability, "other key attributes". Mapping from metafields/metaobjects/tags is configurable (Catalog Mapping). Compare-at price optionally shown.
- Eligibility is a store-side status in the admin ("Ineligible" + reason). Owner-only; an external scanner cannot read it.
- Crawler access: network-layer bot management handled by Shopify; `robots.txt` (editable via robots.txt.liquid) is "directional and advisory".
- Auto-served discovery files on every Shopify store: `/agents.md` (canonical), `/llms.txt`, `/llms-full.txt` — same content by default: store name/URL, sitemap link, policies, discovery endpoints. Overridable by theme templates.
- Developer side: Storefront Catalog MCP at `https://{store}/api/ucp/mcp` (tools `search_catalog`, `lookup_catalog`, `get_product`); requires an agent profile on every request. Global Catalog at catalog.shopify.com. Universal Cart API = early-access waitlist.
- B2B/password/customer-account-gated products are excluded automatically.
- Unlisted product status hides products from AI channels.

### 2b. Google (UCP + Merchant Center, from developers.google.com/merchant/ucp) [V]
- Two integration paths: **Native checkout** or **Cart path** (hand-off to merchant site). **Google approval required** before going live (waitlist). So UCP participation is not self-service, except via Shopify which handles it.
- Merchant publishes a **UCP profile at `/.well-known/ucp`** (JSON: version, services with transport rest/mcp + endpoint, capabilities such as `dev.ucp.shopping.cart|checkout|fulfillment|discount|order`, payment_handlers, signing_keys).
- Prereqs in **Merchant Center** (data requirement, not scannable on-site): product feed, return policy (cost, window, policy link), customer support contact (URL/email/phone), product identifiers, per-product `native_commerce(checkout_eligibility)`.
- Checkout-ineligible categories: subscriptions, installments, personalized goods, used/refurbished/final-sale, pre-orders, bundled services, special-shipping items.
- Google identifies its UCP traffic by header `UCP-Agent: Profile` and a User-Agent beginning `Google/UCP` (FAQ).

### 2c. OpenAI (ACP + feeds, from developers.openai.com/commerce) [V]
- Discovery is **feed-based** (CSV/TSV/XML/JSON; file upload/SFTP or API), not page-scraping-based. Daily snapshot + API upserts, fresh price/availability.
- Required per item (9): `item_id, title, description, url, brand, seller_name, image_url, availability, price`. Guidance: title ≤150 chars, description ≤5,000 chars, plain text, real brand/seller (no placeholders), public https URLs.
- Optional but weighted: `gtin` (8/12/13/14 digits, valid check digit) or `mpn`+brand; returns (`accepts_returns`, `return_deadline_in_days`, `return_policy` URL); shipping; reviews; variant grouping.
- Checkout needs extra fields (`is_eligible_checkout`, `seller_privacy_policy` URL, etc.) and is separately enabled.
- Google-format Merchant Center feeds are accepted (they document a "Google-compatible product data feeds" section).
- Via Shopify, merchants do not build a feed; Shopify Catalog supplies it.

## 3. Live observation (M0 smoke test, 1 request per path, polite UA, public paths only) [L]
- allbirds.com (Shopify): `/.well-known/ucp` → 200 JSON, version 2026-08-25, MCP transport, endpoint `/api/ucp/mcp`, plus older versions linked. `/llms.txt` → 200 (title "Agent Instructions — Allbirds", points to Shop skill + UCP). `/products.json` → 200. robots.txt blocks only SEO/ads bots (Nutch, AhrefsBot, MJ12bot, etc.), not AI agents.
- gymshark.com: `/.well-known/ucp` 404, `/llms.txt` 404 (platform not confirmed Shopify; do not generalize).
- Takeaway: for Shopify stores, UCP profile + llms.txt are **platform-served defaults**, so they will be present on most eligible Shopify stores and have low discriminating power. n=2, to be replaced by the M2 sample.

## 4. What this means for SPEC.md checks

| SPEC check | M0 verdict |
|---|---|
| 1 Structured data (JSON-LD Product/Offer, 30) | **[U]** None of the three primary docs says agents read schema.org JSON-LD from pages. Syndication runs on Catalog/feeds. JSON-LD still matters for ordinary crawlers (Google Search), but the 30 weight is not supported by M0. Reframe as "page data quality / crawler fallback" and cut weight until shown otherwise. |
| 2 Feed/catalog access (15) | Shopify `/products.json` is a public mirror, not what agents consume. Better signals: `/.well-known/ucp` present + valid, `/api/ucp/mcp` reachable, sitemap. Raise weight. |
| 3 Content completeness (20) | **Supported.** Maps directly to OpenAI required fields and Shopify Catalog attributes (title ≤150, description present, image, brand, price, availability). Add GTIN/MPN presence (OpenAI + Google both ask for identifiers). |
| 4 Policy clarity (10) | **Supported.** Google requires return cost/window/link + support contact; OpenAI has return fields; Shopify `agents.md` includes policies. Raise weight. |
| 5 Agent access (15) | robots.txt UA check **supported but advisory** (Shopify says rules are advisory). `llms.txt`/`agents.md`: **real and Shopify-served by default**, so bonus only. Bot-wall check stays. **[U]** exact AI crawler UA tokens (OAI-SearchBot, GPTBot, Google-Extended, etc.): not verified in this pass; pull from each vendor's crawler doc before coding. |
| 6 Checkout signals (10) | **Verified signal exists:** `/.well-known/ucp` (JSON, `ucp.version`, `services`, `capabilities`). Check = present, parses, lists `dev.ucp.shopping.checkout`/`cart`, MCP/REST endpoint reachable. ACP has no on-site discovery endpoint documented. **x402 not covered by any of the three sources**: drop from v0.1. |

New checks to consider: (a) `/agents.md` present; (b) identifier coverage (GTIN/MPN); (c) checkout-ineligible product flags (subscription/final-sale/pre-order) as an informational note.

## 5. Open gaps
- Adoption/impact of Universal Cart or Shopify agentic traffic: no primary data found (**[U]**).
- Whether Google/OpenAI/Perplexity agents read on-page JSON-LD: not stated in docs (**[U]**). Possible test: none cheap; label it an assumption in the write-up.
- Shopify Catalog eligibility requirements page (help.shopify.com/en/manual/shopify-catalog/requirements) not read.
- Did not read UCP catalog/checkout schemas in full (ucp.dev is ~169K chars); only profile shape. Enough for a presence/parse check, not for deep validation.
- Everything is vendor documentation. Treat as "what vendors say they consume", not independent evidence.


## Crawler tokens (verified at vendor docs 2026-10-23) [V]
Scored in check 5 (surface/shop for users; blocking hides the store):
- OpenAI: `OAI-SearchBot` (ChatGPT search results), `ChatGPT-User` (user-initiated fetches; OpenAI says robots.txt "may not apply"). Source: developers.openai.com/api/docs/bots
- Google: `Googlebot` (Search incl. AI features), `Storebot-Google` (all Google Shopping surfaces). Source: developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers (updated 2026-10-15)
- Perplexity: `PerplexityBot` (search), `Perplexity-User` (user fetches; "generally ignores robots.txt"). Source: docs.perplexity.ai/guides/bots
- Anthropic: `Claude-SearchBot`, `Claude-User`. Source: support.claude.com article 8896518
- Apple: `Applebot` (Siri/Spotlight/Safari search). Source: support.apple.com/en-us/119829
Info only (training opt-outs, legitimate owner choice): `GPTBot`, `Google-Extended` (Gemini training; token only, no separate UA), `ClaudeBot`, `Applebot-Extended`.
Not found in the Google crawler list: any Universal-Cart- or AI-Mode-specific token. AI Mode/Universal Cart appear to rely on Googlebot + Merchant Center/UCP [inference].
Caveat: user-initiated fetchers may ignore robots.txt, so a block there is a stated preference, not a guaranteed barrier. Bot walls (WAF/CAPTCHA) are the real barrier; Perplexity docs explicitly tell owners to allowlist its bots in WAFs.
