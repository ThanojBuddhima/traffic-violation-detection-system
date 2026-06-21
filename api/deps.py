"""FastAPI dependencies."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from database.session import get_db as _get_db

get_db = _get_db
