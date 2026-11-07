"""P4 — build the Excel price-comparison sheet from the price-history DB.

Usage: python3 src/build_excel.py   (run from the project folder)
Output: outputs/price-comparison_SAMPLE.xlsx
- 'Comparison' sheet: all books from the latest snapshot, sorted by
  category then price, with snapshot values (not formulas).
- 'Summary' sheet: overall KPIs as live formulas (COUNT, MIN, MAX,
  AVERAGE, COUNTIF) over the Comparison sheet, so the summary moves
  if a user edits a price.
"""
import sqlite3
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
BOLD = Font(bold=True)


def main():
    con = sqlite3.connect(ROOT / "data" / "processed" / "price_history.db")
    rows = con.execute(
        "SELECT b.category, b.title, s.price_gbp, s.rating, s.availability, b.book_url "
        "FROM price_snapshots s JOIN books b ON b.book_url = s.book_url "
        "ORDER BY b.category, s.price_gbp"
    ).fetchall()
    snap = con.execute("SELECT MAX(snapshot_date) FROM price_snapshots").fetchone()[0]
    wb = Workbook()
    ws = wb.active
    ws.title = "Comparison"
    ws.append(["Category", "Title", "Price (£)", "Rating (1-5)", "Availability", "Product URL"])
    for c in ws[1]:
        c.font = BOLD
    for r in rows:
        ws.append(list(r))
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:F{len(rows) + 1}"
    widths = [22, 70, 12, 13, 14, 90]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1

    sm = wb.create_sheet("Summary")
    sm.append(["Price Tracker — Summary (SAMPLE snapshot)", snap])
    sm["A1"].font = BOLD
    sm.append([])
    sm.append(["Metric", "Value (formula over Comparison sheet)"])
    for c in sm[3]:
        c.font = BOLD
    n = len(rows) + 1  # last data row in Comparison
    metrics = [
        ("Books tracked", f"=COUNTA(Comparison!B2:B{n})"),
        ("Categories", f"=SUMPRODUCT(1/COUNTIF(Comparison!A2:A{n},Comparison!A2:A{n}))"),
        ("Cheapest price (£)", f"=MIN(Comparison!C2:C{n})"),
        ("Most expensive (£)", f"=MAX(Comparison!C2:C{n})"),
        ("Average price (£)", f"=ROUND(AVERAGE(Comparison!C2:C{n}),2)"),
        ("5-star books", f"=COUNTIF(Comparison!D2:D{n},5)"),
        ("In-stock books", f"=COUNTIF(Comparison!E2:E{n},\"*In stock*\")"),
    ]
    for label, formula in metrics:
        sm.append([label, formula])
    sm.column_dimensions["A"].width = 26
    sm.column_dimensions["B"].width = 44
    out = ROOT / "outputs" / "price-comparison_SAMPLE.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f"saved {out} ({len(rows)} books, snapshot {snap})")


if __name__ == "__main__":
    main()
