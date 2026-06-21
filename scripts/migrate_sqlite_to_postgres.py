#!/usr/bin/env python3
"""One-time migration helper: SQLite → PostgreSQL (V2).

Usage:
  export SQLITE_URL=sqlite:///./database/violations.db
  export POSTGRES_URL=postgresql://app:password@localhost:5432/violations
  python scripts/migrate_sqlite_to_postgres.py
"""

import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Video, Violation


def migrate():
    sqlite_url = os.environ.get("SQLITE_URL", "sqlite:///./database/violations.db")
    postgres_url = os.environ.get("POSTGRES_URL")
    if not postgres_url:
        print("POSTGRES_URL environment variable required", file=sys.stderr)
        sys.exit(1)

    src_engine = create_engine(sqlite_url)
    dst_engine = create_engine(postgres_url)

    Base.metadata.create_all(bind=dst_engine)

    SrcSession = sessionmaker(bind=src_engine)
    DstSession = sessionmaker(bind=dst_engine)

    src = SrcSession()
    dst = DstSession()

    try:
        for video in src.query(Video).all():
            dst.merge(video)
        for violation in src.query(Violation).all():
            dst.merge(violation)
        dst.commit()
        print(f"Migrated {src.query(Video).count()} videos and {src.query(Violation).count()} violations")
    finally:
        src.close()
        dst.close()


if __name__ == "__main__":
    migrate()
