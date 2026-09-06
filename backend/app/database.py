"""Small MySQL connection helper for the Phase 1 region dashboard."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import mysql.connector
from mysql.connector import MySQLConnection

from app.config import settings


@contextmanager
def connection() -> Iterator[MySQLConnection]:
    database_connection = mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=settings.mysql_database,
        user=settings.mysql_user,
        password=settings.mysql_password,
    )
    try:
        yield database_connection
    finally:
        database_connection.close()
