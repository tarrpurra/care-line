from contextlib import contextmanager
import sqlite3
from collections.abc import Iterator

from config import settings


def connect() -> sqlite3.Connection:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.database_path, timeout=10, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


@contextmanager
def transaction(*, immediate: bool = False) -> Iterator[sqlite3.Connection]:
    connection = connect()
    try:
        connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
