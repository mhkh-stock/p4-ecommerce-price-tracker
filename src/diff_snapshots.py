"""P4 — compare the two latest price snapshots and write a change report.

Usage: python3 src/diff_snapshots.py [--db PATH] [--out PATH]

Read-only on the database: it never writes to the DB. It compares the
two most recent snapshot dates and writes outputs/price-changes.md with
price moves (up/down), new and removed products, availability changes,
and category average moves. With only one snapshot date there is
nothing to compare yet, so it prints a note and writes nothing.
"""
import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "processed" / "price_history.db"
DEFAULT_OUT = ROOT / "outputs" / "price-changes.md"
LIST_CAP = 100


def main():
    ap = argparse.ArgumentParser(description="Diff the two latest price snapshots.")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    dates = [r[0] for r in con.execute(
        "SELECT DISTINCT snapshot_date FROM price_snapshots ORDER BY snapshot_date")]
    if len(dates) < 2:
        only = dates[0] if dates else "none"
        print(f"Only one snapshot ({only}) — nothing to compare yet.")
        print("Re-run src/scrape_prices.py on another day, then run this again.")
        return 0
    old, new = dates[-2], dates[-1]

    moved = con.execute(
        "SELECT b.title, b.category, o.price_gbp, n.price_gbp, "
        "ROUND(n.price_gbp - o.price_gbp, 2) "
        "FROM price_snapshots o JOIN price_snapshots n ON n.book_url = o.book_url "
        "JOIN books b ON b.book_url = n.book_url "
        "WHERE o.snapshot_date = ? AND n.snapshot_date = ? AND o.price_gbp != n.price_gbp "
        "ORDER BY (n.price_gbp - o.price_gbp) DESC", (old, new)).fetchall()
    added = con.execute(
        "SELECT b.title, b.category, n.price_gbp FROM price_snapshots n "
        "JOIN books b ON b.book_url = n.book_url "
        "WHERE n.snapshot_date = ? AND n.book_url NOT IN "
        "(SELECT book_url FROM price_snapshots WHERE snapshot_date = ?) "
        "ORDER BY b.category, n.price_gbp", (new, old)).fetchall()
    removed = con.execute(
        "SELECT b.title, b.category, o.price_gbp FROM price_snapshots o "
        "JOIN books b ON b.book_url = o.book_url "
        "WHERE o.snapshot_date = ? AND o.book_url NOT IN "
        "(SELECT book_url FROM price_snapshots WHERE snapshot_date = ?) "
        "ORDER BY b.category, o.price_gbp", (old, new)).fetchall()
    stock = con.execute(
        "SELECT b.title, b.category, o.availability, n.availability "
        "FROM price_snapshots o JOIN price_snapshots n ON n.book_url = o.book_url "
        "JOIN books b ON b.book_url = n.book_url "
        "WHERE o.snapshot_date = ? AND n.snapshot_date = ? "
        "AND o.availability IS NOT n.availability "
        "ORDER BY b.category, b.title", (old, new)).fetchall()
    cat_avg = con.execute(
        "SELECT b.category, ROUND(AVG(o.price_gbp), 2), ROUND(AVG(n.price_gbp), 2), "
        "ROUND(AVG(n.price_gbp) - AVG(o.price_gbp), 2) "
        "FROM price_snapshots o JOIN price_snapshots n ON n.book_url = o.book_url "
        "JOIN books b ON b.book_url = n.book_url "
        "WHERE o.snapshot_date = ? AND n.snapshot_date = ? "
        "GROUP BY b.category HAVING AVG(n.price_gbp) != AVG(o.price_gbp) "
        "ORDER BY (AVG(n.price_gbp) - AVG(o.price_gbp)) DESC", (old, new)).fetchall()
    con.close()

    ups = [m for m in moved if m[4] > 0]
    downs = [m for m in moved if m[4] < 0]
    lines = [f"# Price changes — {old} → {new} (SAMPLE)",
             "",
             f"- Prices moved: **{len(moved)}** of the books in both snapshots "
             f"({len(ups)} up, {len(downs)} down)",
             f"- New products: **{len(added)}** · Removed products: **{len(removed)}**",
             f"- Availability changed: **{len(stock)}**",
             f"- Categories whose average moved: **{len(cat_avg)}**",
             ""]
    def table(title, header, rows, fmt):
        lines.append(f"## {title}")
        lines.append("")
        if not rows:
            lines.append("None.")
            lines.append("")
            return
        lines.append(header)
        lines.append("|" + " --- |" * (header.count("|") - 1))
        for r in rows[:LIST_CAP]:
            lines.append(fmt(r))
        if len(rows) > LIST_CAP:
            lines.append(f"\n…plus {len(rows) - LIST_CAP} more (see the database).")
        lines.append("")
    table(f"Price moves ({len(moved)})", "| Title | Category | Before (£) | After (£) | Change (£) |",
          moved, lambda r: f"| {r[0]} | {r[1]} | {r[2]:.2f} | {r[3]:.2f} | {r[4]:+.2f} |")
    table(f"New products ({len(added)})", "| Title | Category | Price (£) |",
          added, lambda r: f"| {r[0]} | {r[1]} | {r[2]:.2f} |")
    table(f"Removed products ({len(removed)})", "| Title | Category | Last price (£) |",
          removed, lambda r: f"| {r[0]} | {r[1]} | {r[2]:.2f} |")
    table(f"Availability changes ({len(stock)})", "| Title | Category | Before | After |",
          stock, lambda r: f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |")
    table(f"Category average moves ({len(cat_avg)})", "| Category | Avg before (£) | Avg after (£) | Change (£) |",
          cat_avg, lambda r: f"| {r[0]} | {r[1]:.2f} | {r[2]:.2f} | {r[3]:+.2f} |")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"compared {old} → {new}: {len(moved)} price moves, "
          f"{len(added)} new, {len(removed)} removed, {len(stock)} stock changes")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
