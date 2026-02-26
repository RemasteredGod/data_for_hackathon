#!/usr/bin/env python3
"""Scrape registration title details from prgi.gov.in.

Example:
  python scrape_prgi.py --start-page 1 --end-page 77 --items-per-page 1000 --output prgi_77000.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import time
from typing import Dict, Iterable, List, Optional

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://prgi.gov.in/registration-title-details"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(DEFAULT_HEADERS)
    return session


def page_params(page: int, items_per_page: int) -> Dict[str, str]:
    return {
        "title_name": "",
        "registration_number": "",
        "owner_name": "",
        "pub_state_name": "",
        "pub_dist_name": "",
        "languages": "",
        "items_per_page": str(items_per_page),
        "page": str(page),
    }


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def parse_table_from_html(html: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")

    table = soup.select_one("table")
    if table is None:
        return []

    headers = [clean_text(th.get_text(" ", strip=True)) for th in table.select("thead th")]
    if not headers:
        first_row = table.select_one("tr")
        if first_row:
            headers = [clean_text(cell.get_text(" ", strip=True)) for cell in first_row.find_all(["th", "td"]) ]

    rows: List[Dict[str, str]] = []
    body_rows = table.select("tbody tr") or table.select("tr")[1:]

    for tr in body_rows:
        cells = tr.find_all("td")
        if not cells:
            continue
        values = [clean_text(td.get_text(" ", strip=True)) for td in cells]
        if headers and len(headers) == len(values):
            row = dict(zip(headers, values))
        else:
            row = {f"col_{i+1}": val for i, val in enumerate(values)}
        rows.append(row)

    return rows


def fetch_page(session: requests.Session, page: int, items_per_page: int, timeout: int) -> List[Dict[str, str]]:
    response = session.get(BASE_URL, params=page_params(page, items_per_page), timeout=timeout)
    response.raise_for_status()
    rows = parse_table_from_html(response.text)

    if not rows:
        # Some sites embed data in JS; try extracting JSON arrays from scripts as fallback.
        script_json_match = re.search(r"(\[\s*\{.*?\}\s*\])", response.text, flags=re.S)
        if script_json_match:
            try:
                data = json.loads(script_json_match.group(1))
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    rows = [{k: clean_text(str(v)) for k, v in item.items()} for item in data]
            except json.JSONDecodeError:
                pass

    return rows


def dedupe(rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    unique: List[Dict[str, str]] = []
    seen = set()
    for row in rows:
        key = tuple(sorted(row.items()))
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def write_csv(path: str, rows: List[Dict[str, str]]) -> None:
    if not rows:
        raise ValueError("No rows to write")

    all_columns = []
    seen = set()
    for row in rows:
        for col in row.keys():
            if col not in seen:
                seen.add(col)
                all_columns.append(col)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape prgi.gov.in registration title details")
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--end-page", type=int, default=77)
    parser.add_argument("--items-per-page", type=int, default=1000)
    parser.add_argument("--output", default="prgi_registration_title_details.csv")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--min-delay", type=float, default=0.8, help="Minimum delay between page requests")
    parser.add_argument("--max-delay", type=float, default=1.8, help="Maximum delay between page requests")
    parser.add_argument("--no-dedupe", action="store_true", help="Keep duplicate rows")
    args = parser.parse_args()

    if args.start_page < 1 or args.end_page < args.start_page:
        raise SystemExit("Invalid page range")

    session = build_session()
    collected: List[Dict[str, str]] = []

    for page in range(args.start_page, args.end_page + 1):
        print(f"Fetching page {page}/{args.end_page} ...")
        try:
            rows = fetch_page(session, page=page, items_per_page=args.items_per_page, timeout=args.timeout)
        except requests.RequestException as exc:
            print(f"  Failed page {page}: {exc}")
            continue

        if not rows:
            print(f"  No rows found on page {page}")
        else:
            print(f"  Got {len(rows)} rows")
            collected.extend(rows)

        time.sleep(random.uniform(args.min_delay, args.max_delay))

    if not collected:
        raise SystemExit("No data collected. Inspect the page HTML/API, it may require different parsing.")

    if not args.no_dedupe:
        before = len(collected)
        collected = dedupe(collected)
        print(f"Deduplicated: {before} -> {len(collected)}")

    write_csv(args.output, collected)
    print(f"Saved {len(collected)} rows to {args.output}")


if __name__ == "__main__":
    main()
