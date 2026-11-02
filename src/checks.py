"""P4 data-quality checks as code. Run: python3 src/checks.py
Exits non-zero if any check fails. All checks must pass before delivery.
"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
con = sqlite3.connect(ROOT / "data" / "processed" / "price_history.db")
fails = []


def check(name, sql, expect):
    got = con.execute(sql).fetchone()[0]
    ok = got == expect
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {got}, expected {expect}")
    if not ok:
        fails.append(name)


check("books = 1000", "SELECT COUNT(*) FROM books", 1000)
check("snapshots = 1000 (one per book, one snapshot date)",
      "SELECT COUNT(*) FROM price_snapshots", 1000)
check("exactly one snapshot date",
      "SELECT COUNT(DISTINCT snapshot_date) FROM price_snapshots", 1)
check("categories = 50", "SELECT COUNT(DISTINCT category) FROM books", 50)
check("no null/zero prices",
      "SELECT COUNT(*) FROM price_snapshots WHERE price_gbp IS NULL OR price_gbp <= 0", 0)
check("no missing ratings",
      "SELECT COUNT(*) FROM price_snapshots WHERE rating IS NULL OR rating NOT BETWEEN 1 AND 5", 0)
check("every snapshot has a book row",
      "SELECT COUNT(*) FROM price_snapshots s LEFT JOIN books b ON b.book_url=s.book_url WHERE b.book_url IS NULL", 0)
check("every book URL is a catalogue URL",
      "SELECT COUNT(*) FROM books WHERE book_url NOT LIKE '%/catalogue/%'", 0)
check("no duplicate book URLs",
      "SELECT COUNT(*) - COUNT(DISTINCT book_url) FROM books", 0)
print("ALL CHECKS PASSED" if not fails else f"{len(fails)} CHECK(S) FAILED")
sys.exit(1 if fails else 0)
