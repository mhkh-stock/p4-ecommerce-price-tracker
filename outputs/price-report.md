# Price report — books.toscrape.com snapshot, 31 Oct 2026 (SAMPLE)

Scope: the site's full catalogue — 1,000 books across 50 categories,
scraped category by category in one polite run (0.25s between requests).

## Headline numbers

- Books tracked: 1,000 · Categories: 50
- Price range: £10.00 – £59.99 · Average: £35.07
- Cheapest: *An Abundance of Katherines* (£10.00)
- Priciest: *The Perfect Play (Play by Play #1)* (£59.99)
- Ratings: 1★ 226 · 2★ 196 · 3★ 203 · 4★ 179 · 5★ 196
- In stock: 1,000 / 1,000

## What this snapshot proves about the tracker

1. **Full coverage, not a sample of a sample.** All 50 categories and
   all 1,000 books landed in one run — the same run a client order
   would use on their competitor's catalogue.
2. **History, not just today.** Prices live in dated snapshots, so the
   next run answers "what changed?" without re-scraping history.
3. **Clean on arrival.** 9 automated checks pass: no missing prices,
   no missing ratings, no duplicate products, every URL a live
   catalogue URL (one spot-checked live, HTTP 200).

## What a client does with the next run

Re-run the scraper, rebuild the sheet, and compare the two snapshots:
new prices, items that went out of stock, and categories whose average
moved. That diff — not a fresh list — is the report a pricing manager
actually acts on.
