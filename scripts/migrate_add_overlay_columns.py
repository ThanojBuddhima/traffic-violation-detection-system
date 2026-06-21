#!/usr/bin/env python3
"""Add overlay/plate columns to existing SQLite database."""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.config import settings

MIGRATIONS = [
    ("videos", "width", "INTEGER"),
    ("videos", "height", "INTEGER"),
    ("violations", "plate_image_path", "VARCHAR(1024)"),
    ("violations", "overlay_frames", "TEXT DEFAULT '[]'"),
]


def column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def main() -> None:
    if not settings.DATABASE_URL.startswith("sqlite"):
        print("This migration script only supports SQLite.")
        sys.exit(1)

    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    path = Path(db_path)
    if not path.exists():
        print(f"Database not found: {path} — run the app first to create it.")
        sys.exit(0)

    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    applied = 0
    for table, column, col_type in MIGRATIONS:
        if column_exists(cursor, table, column):
            print(f"Skip {table}.{column} (already exists)")
            continue
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"Added {table}.{column}")
        applied += 1
    conn.commit()
    conn.close()
    print(f"Done. {applied} column(s) added.")


if __name__ == "__main__":
    main()
