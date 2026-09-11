#!/usr/bin/env python3
"""
Preprocess the Union Scene Facebook feed for Smartly.

- Fetches the source CSV
- Explodes multi-category rows into one (event x category) pair per category
- Counts events per category
- Writes ONE summary row where each column is a category name and the
  value is Active / Paused based on MIN_EVENTS threshold

Output is written to output/facebook_smartly.csv (Smartly-ready):

  Popglade,Rock,Viser,...
  Active,Paused,Active,...

Config via environment variables:
  SOURCE_URL   source CSV url (has a sensible default)
  MIN_EVENTS   threshold for Active (default: 3)
  OUTPUT_PATH  where to write the processed feed
"""

import ast
import csv
import io
import os
import sys
import urllib.request
from collections import Counter

SOURCE_URL = os.environ.get(
    "SOURCE_URL",
    "https://unionscene.no/wp-content/uploads/ambio-marketing/csv/facebook.csv",
)
MIN_EVENTS = int(os.environ.get("MIN_EVENTS", "3"))
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "output/facebook_smartly.csv")

# Column in the source that holds the category list, e.g. "['Pop','Viser']"
CATEGORY_COL = "Kategorier"


def fetch_csv(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "smartly-feed-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    # Source is served as UTF-8
    return raw.decode("utf-8")


def parse_categories(value: str) -> list:
    """Parse "['Pop','Viser']" into ['Pop', 'Viser']. Robust to junk."""
    value = (value or "").strip()
    if not value:
        return []
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, (list, tuple)):
            return [str(c).strip() for c in parsed if str(c).strip()]
        if isinstance(parsed, str) and parsed.strip():
            return [parsed.strip()]
    except (ValueError, SyntaxError):
        # Fallback: strip brackets/quotes and split on comma
        cleaned = value.strip("[]")
        parts = [p.strip().strip("'\"") for p in cleaned.split(",")]
        return [p for p in parts if p]
    return []


def main() -> int:
    try:
        text = fetch_csv(SOURCE_URL)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: failed to fetch source feed: {exc}", file=sys.stderr)
        return 1

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or CATEGORY_COL not in reader.fieldnames:
        print(
            f"ERROR: source feed missing '{CATEGORY_COL}' column. "
            f"Got: {reader.fieldnames}",
            file=sys.stderr,
        )
        return 1

    rows = list(reader)
    if not rows:
        print("ERROR: source feed has no data rows.", file=sys.stderr)
        return 1

    # Count events per category
    counts = Counter()
    for row in rows:
        for cat in parse_categories(row.get(CATEGORY_COL, "")):
            counts[cat] += 1

    if not counts:
        print("ERROR: no categories found after parsing.", file=sys.stderr)
        return 1

    # One column per category, sorted for a stable header order across runs
    categories = sorted(counts, key=lambda c: c.casefold())
    status = {
        cat: ("Active" if counts[cat] >= MIN_EVENTS else "Paused") for cat in categories
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=categories, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerow(status)

    # Summary to stdout (visible in Actions logs)
    active = sum(1 for s in status.values() if s == "Active")
    paused = len(status) - active
    print(f"Source rows:        {len(rows)}")
    print(f"Categories:         {len(counts)} ({active} Active / {paused} Paused)")
    print(f"Threshold MIN_EVENTS={MIN_EVENTS}")
    print(f"Output:             {OUTPUT_PATH}")
    print("\nPer-category counts:")
    for cat in sorted(counts, key=lambda c: (-counts[c], c.casefold())):
        print(f"  {counts[cat]:>3}  {status[cat]:<7} {cat}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
