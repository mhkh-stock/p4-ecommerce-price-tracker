# Data dictionary — P4 price tracker (SAMPLE snapshot, 31 Oct 2026)

## Database: `data/processed/price_history.db`

### `books` — one row per product ever seen

| Column | Type | Meaning |
|---|---|---|
| book_url | text (PK) | Product page URL on books.toscrape.com (all contain `/catalogue/`) |
| title | text | Product title as listed |
| category | text | One of the site's 50 categories |
| first_seen | date | First snapshot date this product appeared on |

### `price_snapshots` — one row per product per run date

| Column | Type | Meaning |
|---|---|---|
| snapshot_date | date (PK part) | Run date, ISO `YYYY-MM-DD` |
| book_url | text (PK part, FK → books) | Product page URL |
| price_gbp | real | Listed price in GBP, always > 0 |
| rating | int 1–5 | Star rating as listed (One=1 … Five=5) |
| availability | text | Availability text as listed (e.g. "In stock") |

Re-running the scraper inserts a new `snapshot_date`; old rows are
never updated, so `price_snapshots` for two dates shows exactly what
moved. The Excel sheet is built from the latest snapshot only.

## Excel: `outputs/price-comparison_SAMPLE.xlsx`

- `Comparison`: category, title, price (£), rating, availability,
  product URL — sorted by category, then price ascending.
- `Summary`: live formulas (COUNT, MIN, MAX, AVERAGE, COUNTIF) over
  the Comparison sheet — edit a price and the summary moves.
