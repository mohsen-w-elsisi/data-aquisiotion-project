from typing import Callable
import sqlite3
import json

_CACH_DB_PATH = "cache.db"


def _db_operation(func: Callable):
    def wrapper(*args):
        db_connection = sqlite3.connect(_CACH_DB_PATH)
        cursor = db_connection.cursor()
        if not _is_cache_inited(cursor):
            _init_cache(cursor)

        res = func(cursor, *args)

        db_connection.commit()
        db_connection.close()
        return res

    return wrapper


def _is_cache_inited(cursor: sqlite3.Cursor):
    res = cursor.execute(
        """
        SELECT name FROM sqlite_master WHERE name='listings'
    """
    ).fetchone()
    return res is not None


def _init_cache(cursor: sqlite3.Cursor):
    cursor.execute(
        """
            CREATE TABLE listings (
                product_name TEXT PRIMARY KEY,
                listings_json TEXT
            )
        """
    )


@_db_operation
def set_cached(cursor: sqlite3.Cursor, product_name: str, listings_json: dict):
    cursor.execute(
        """
        INSERT INTO listings (product_name, listings_json)
        VALUES (?, ?)
    """,
        (product_name, json.dumps(listings_json)),
    )


@_db_operation
def get_cached(cursor: sqlite3.Cursor, product_name: str):
    res = cursor.execute(
        """
        SELECT listings_json FROM listings WHERE product_name = ?
        """,
        (product_name,),
    ).fetchone()
    return json.loads(res[0]) if res is not None else None
