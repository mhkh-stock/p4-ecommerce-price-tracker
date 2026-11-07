-- P4 price-history schema (SQLite).
-- books = one row per product (ever seen). price_snapshots = one row per
-- product per snapshot date. A re-run on a NEW date adds a snapshot and
-- never overwrites history, so price changes are visible as
-- snapshot-vs-snapshot differences; re-running on the SAME date
-- refreshes that day's snapshot (INSERT OR REPLACE in the scraper).
CREATE TABLE IF NOT EXISTS books (
    book_url TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    first_seen TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS price_snapshots (
    snapshot_date TEXT NOT NULL,
    book_url TEXT NOT NULL REFERENCES books(book_url),
    price_gbp REAL NOT NULL CHECK (price_gbp > 0),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    availability TEXT,
    PRIMARY KEY (snapshot_date, book_url)
);
