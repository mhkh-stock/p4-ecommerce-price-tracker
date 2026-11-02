"""P4 — E-commerce Price Tracker (SAMPLE snapshot).

Scrapes books.toscrape.com — a site built explicitly for scraping
practice — category by category, and stores every book with its price
in a SQLite price-history database. Re-running the script adds a new
snapshot dated today, so price changes show up as snapshot-vs-snapshot
differences instead of overwriting history.

Politeness: one request at a time, 0.25s between requests, a clearly
labelled User-Agent, no login, no form submission, and only the public
catalogue pages. For a real client order, point CATEGORY_INDEX at the
client's own competitor URLs (with their permission) — the parser and
the database stay the same.

Stdlib only (urllib + html.parser), so it runs anywhere Python runs.
Usage: python3 src/scrape_prices.py   (run from the project folder)
"""
import sqlite3
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://books.toscrape.com/"
INDEX = BASE + "catalogue/category/books_1/index.html"
UA = "HashirPortfolioDemo/1.0 (price-tracker sample; practice-site only)"
DELAY = 0.25
RATING = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:
            if attempt == 1:
                raise
            print(f"  retry {url}: {e}")
            time.sleep(1)
    return ""


class CategoryParser(HTMLParser):
    """Sidebar category links: href contains '/category/books/'."""

    def __init__(self):
        super().__init__()
        self.cats = []
        self._href = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            d = dict(attrs)
            # Sidebar links look like ../books/travel_2/index.html
            if "/books/" in d.get("href", "") and d["href"].endswith("index.html"):
                self._href = d["href"]

    def handle_data(self, data):
        if self._href:
            name = data.strip()
            if name and name != "Books":
                self.cats.append((name, urljoin(INDEX, self._href)))
            self._href = None


class BookParser(HTMLParser):
    """One page of product pods: title, price, rating, availability, link."""

    def __init__(self, page_url):
        super().__init__()
        self.page_url = page_url
        self.books = []
        self._in_pod = False
        self._cur = None
        self._field = None

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "article" and "product_pod" in d.get("class", ""):
            self._in_pod = True
            self._cur = {}
        if not self._in_pod:
            return
        if tag == "a" and "title" in d:
            self._cur["title"] = d["title"]
            self._cur["url"] = urljoin(self.page_url, d["href"])
        if tag == "p" and "price_color" in d.get("class", ""):
            self._field = "price"
        elif tag == "p" and "star-rating" in d.get("class", ""):
            for word, num in RATING.items():
                if word in d["class"]:
                    self._cur["rating"] = num
        elif tag == "p" and "instock" in d.get("class", ""):
            self._field = "availability"

    def handle_data(self, data):
        if self._field == "price":
            self._cur["price"] = float(data.strip().replace("£", ""))
            self._field = None
        elif self._field == "availability":
            txt = data.strip()
            if txt:
                self._cur["availability"] = txt
                self._field = None

    def handle_endtag(self, tag):
        if tag == "article" and self._in_pod:
            if self._cur and "price" in self._cur:
                self.books.append(self._cur)
            self._in_pod = False
            self._cur = None


def scrape_category(name, url):
    """Follow a category's pagination until no 'next' page exists."""
    books, page_url, page_no = [], url, 1
    while page_url:
        html = fetch(page_url)
        parser = BookParser(page_url)
        parser.feed(html)
        for b in parser.books:
            b["category"] = name
        books.extend(parser.books)
        print(f"  {name} p{page_no}: {len(parser.books)} books")
        time.sleep(DELAY)
        if 'class="next"' in html:
            nxt = page_url.rsplit("/", 1)[0] + f"/page-{page_no + 1}.html"
            page_url, page_no = nxt, page_no + 1
        else:
            page_url = None
    return books


def main():
    (ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    cats_html = fetch(INDEX)
    cat_parser = CategoryParser()
    cat_parser.feed(cats_html)
    cats = cat_parser.cats
    print(f"categories found: {len(cats)}")
    all_books = []
    for name, url in cats:
        all_books.extend(scrape_category(name, url))
    # Deduplicate by URL (a book appears in exactly one category, but be safe).
    seen, books = set(), []
    for b in all_books:
        if b["url"] not in seen:
            seen.add(b["url"])
            books.append(b)
    print(f"total unique books: {len(books)}")

    db_path = ROOT / "data" / "processed" / "price_history.db"
    con = sqlite3.connect(db_path)
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    today = time.strftime("%Y-%m-%d")
    for b in books:
        con.execute(
            "INSERT INTO books (book_url, title, category, first_seen) "
            "VALUES (?, ?, ?, ?) ON CONFLICT(book_url) DO UPDATE SET "
            "title=excluded.title, category=excluded.category",
            (b["url"], b["title"], b["category"], today))
        con.execute(
            "INSERT OR REPLACE INTO price_snapshots "
            "(snapshot_date, book_url, price_gbp, rating, availability) "
            "VALUES (?, ?, ?, ?, ?)",
            (today, b["url"], b["price"], b.get("rating"), b.get("availability", "")))
    con.commit()
    print(f"snapshot {today}: {len(books)} rows written to {db_path}")
    con.close()


if __name__ == "__main__":
    main()
