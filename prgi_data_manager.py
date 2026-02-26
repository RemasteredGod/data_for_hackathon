#!/usr/bin/env python3
"""PRGI data database management and filtering utility.

Typical flow:
  1) Import scraped CSV into SQLite DB
     python prgi_data_manager.py import --csv prgi_77000.csv --db prgi_data.db

  2) Filter records and print/save
     python prgi_data_manager.py query --db prgi_data.db --state Maharashtra --language Hindi --limit 50
     python prgi_data_manager.py query --db prgi_data.db --owner "Ramesh" --export filtered.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

TABLE_NAME = "registrations"

# Canonical columns for a normalized table. Extra fields from CSV are stored in meta_json.
CANONICAL_COLUMNS = [
    "sr_no",
    "title_name",
    "registration_number",
    "owner_name",
    "pub_state_name",
    "pub_dist_name",
    "language",
    "class_name",
]

ALIASES = {
    "sr no": "sr_no",
    "s.no": "sr_no",
    "s no": "sr_no",
    "title": "title_name",
    "title name": "title_name",
    "registration no": "registration_number",
    "registration number": "registration_number",
    "owner": "owner_name",
    "owner name": "owner_name",
    "state": "pub_state_name",
    "publication state": "pub_state_name",
    "district": "pub_dist_name",
    "publication district": "pub_dist_name",
    "language": "language",
    "languages": "language",
    "class": "class_name",
    "class name": "class_name",
}


def normalize_header(name: str) -> str:
    if name is None or not name:
        return ""
    key = " ".join(name.strip().lower().replace("_", " ").split())
    return ALIASES.get(key, key.replace(" ", "_"))


def connect_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sr_no TEXT,
            title_name TEXT,
            registration_number TEXT,
            owner_name TEXT,
            pub_state_name TEXT,
            pub_dist_name TEXT,
            language TEXT,
            class_name TEXT,
            meta_json TEXT
        )
        """
    )
    conn.execute(
        f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{TABLE_NAME}_unique ON {TABLE_NAME} (registration_number, title_name, owner_name)"
    )
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_state ON {TABLE_NAME} (pub_state_name)")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_dist ON {TABLE_NAME} (pub_dist_name)")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_language ON {TABLE_NAME} (language)")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_owner ON {TABLE_NAME} (owner_name)")
    conn.commit()
    return conn


def row_to_canonical(row: Dict[str, str]) -> Dict[str, str]:
    normalized = {normalize_header(k): (v or "").strip() for k, v in row.items() if k}
    # Remove empty keys from normalization
    normalized = {k: v for k, v in normalized.items() if k}
    canonical = {key: normalized.get(key, "") for key in CANONICAL_COLUMNS}
    extras = {k: v for k, v in normalized.items() if k not in CANONICAL_COLUMNS and v}
    canonical["meta_json"] = "" if not extras else json.dumps(extras, ensure_ascii=False)
    return canonical


def import_csv(conn: sqlite3.Connection, csv_path: str, batch_size: int = 1000) -> Tuple[int, int]:
    inserted = 0
    skipped = 0
    insert_sql = f"""
        INSERT OR IGNORE INTO {TABLE_NAME}
        (sr_no, title_name, registration_number, owner_name, pub_state_name, pub_dist_name, language, class_name, meta_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        batch: List[Tuple[str, ...]] = []

        for row in reader:
            c = row_to_canonical(row)
            batch.append(
                (
                    c["sr_no"],
                    c["title_name"],
                    c["registration_number"],
                    c["owner_name"],
                    c["pub_state_name"],
                    c["pub_dist_name"],
                    c["language"],
                    c["class_name"],
                    c["meta_json"],
                )
            )

            if len(batch) >= batch_size:
                before = conn.total_changes
                conn.executemany(insert_sql, batch)
                conn.commit()
                delta = conn.total_changes - before
                inserted += delta
                skipped += len(batch) - delta
                batch.clear()

        if batch:
            before = conn.total_changes
            conn.executemany(insert_sql, batch)
            conn.commit()
            delta = conn.total_changes - before
            inserted += delta
            skipped += len(batch) - delta

    return inserted, skipped


def build_where_clause(args: argparse.Namespace) -> Tuple[str, List[str]]:
    clauses: List[str] = []
    params: List[str] = []

    def add_like(field: str, value: str) -> None:
        if value:
            clauses.append(f"LOWER({field}) LIKE LOWER(?)")
            params.append(f"%{value.strip()}%")

    def add_eq(field: str, value: str) -> None:
        if value:
            clauses.append(f"LOWER({field}) = LOWER(?)")
            params.append(value.strip())

    add_like("title_name", args.title)
    add_like("owner_name", args.owner)
    add_like("registration_number", args.registration_number)
    add_eq("pub_state_name", args.state)
    add_eq("pub_dist_name", args.district)
    add_eq("language", args.language)
    add_eq("class_name", args.class_name)

    where = " AND ".join(clauses)
    return where, params


def query_data(conn: sqlite3.Connection, args: argparse.Namespace) -> List[sqlite3.Row]:
    where, params = build_where_clause(args)
    sql = f"SELECT * FROM {TABLE_NAME}"
    if where:
        sql += f" WHERE {where}"
    sql += " ORDER BY id ASC"
    if args.limit:
        sql += " LIMIT ?"
        params.append(str(args.limit))

    cur = conn.execute(sql, params)
    return cur.fetchall()


def export_rows(rows: Sequence[sqlite3.Row], out_path: str) -> None:
    if not rows:
        Path(out_path).write_text("", encoding="utf-8")
        return

    headers = rows[0].keys()
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([row[h] for h in headers])


def print_rows(rows: Sequence[sqlite3.Row], max_print: int = 20) -> None:
    if not rows:
        print("No records found.")
        return

    print(f"Found {len(rows)} record(s).")
    for idx, row in enumerate(rows[:max_print], start=1):
        print(
            f"{idx}. Reg#: {row['registration_number']} | Title: {row['title_name']} | "
            f"Owner: {row['owner_name']} | State: {row['pub_state_name']} | "
            f"District: {row['pub_dist_name']} | Language: {row['language']}"
        )
    if len(rows) > max_print:
        print(f"... showing first {max_print}. Use --export to save full results.")


def cmd_import(args: argparse.Namespace) -> None:
    conn = connect_db(args.db)
    inserted, skipped = import_csv(conn, args.csv)
    total = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
    print(f"Import complete. Inserted={inserted}, Skipped(duplicates)={skipped}, Total in DB={total}")
    conn.close()


def cmd_query(args: argparse.Namespace) -> None:
    conn = connect_db(args.db)
    rows = query_data(conn, args)
    print_rows(rows, max_print=args.max_print)
    if args.export:
        export_rows(rows, args.export)
        print(f"Exported {len(rows)} rows to {args.export}")
    conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PRGI database management and filtering tool")
    sub = parser.add_subparsers(dest="command", required=True)

    p_import = sub.add_parser("import", help="Import CSV data into SQLite DB")
    p_import.add_argument("--csv", required=True, help="Input CSV file produced by scraper")
    p_import.add_argument("--db", default="prgi_data.db", help="SQLite DB file path")
    p_import.set_defaults(func=cmd_import)

    p_query = sub.add_parser("query", help="Filter/query records from SQLite DB")
    p_query.add_argument("--db", default="prgi_data.db", help="SQLite DB file path")
    p_query.add_argument("--title", default="", help="Title contains (case-insensitive)")
    p_query.add_argument("--owner", default="", help="Owner name contains")
    p_query.add_argument("--registration-number", default="", help="Registration number contains")
    p_query.add_argument("--state", default="", help="State exact match (case-insensitive)")
    p_query.add_argument("--district", default="", help="District exact match (case-insensitive)")
    p_query.add_argument("--language", default="", help="Language exact match (case-insensitive)")
    p_query.add_argument("--class-name", default="", help="Class exact match (case-insensitive)")
    p_query.add_argument("--limit", type=int, default=100, help="Max rows to return")
    p_query.add_argument("--max-print", type=int, default=20, help="Max rows to print to terminal")
    p_query.add_argument("--export", default="", help="Optional CSV export path for filtered results")
    p_query.set_defaults(func=cmd_query)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
