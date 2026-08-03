import polars as pl

from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from time import sleep


@dataclass
class BookRecord:
    alert_id: int       # アラートID
    category: str       # カテゴリー: 漫画 or ラノベ or 電子書籍
    title: str          # タイトル
    calendar_title: str # カレンダー登録用タイトル
    volume: int         # 最新巻
    release_date: str   # 発売日


def load_db(db_path: Path) -> list[BookRecord]:
    table = pl.read_excel(db_path)

    book_db = []

    for row in table.iter_rows(named=True):
        book = BookRecord(
            alert_id = row["アラートID"],
            category = row["カテゴリー"],
            title = row["タイトル"],
            calendar_title = row["カレンダー用タイトル"],
            volume = row["最新巻"],
            release_date = row["発売日"]
        )

        book_db.append(book)

    return book_db


def save_db(book_db: list[BookRecord], db_path: Path):
    rows = []

    for book in book_db:
        rows.append({
            "アラートID": book.alert_id,
            "カテゴリー": book.category,
            "タイトル": book.title,
            "カレンダー用タイトル": book.calendar_title,
            "最新巻": book.volume,
            "発売日": book.release_date
        })

    table = pl.DataFrame(rows).unique().sort("タイトル", "カテゴリー")
    table.write_excel(db_path)


def retry(
        n_retry: int = 10,
        interval: float = 5,
        exceptions: tuple = (Exception,)
    ):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(n_retry):
                try:
                    return func(*args, **kwargs)

                except exceptions:
                    if attempt == n_retry:
                        raise

                    if interval > 0:
                        sleep(interval)

        return wrapper

    return decorator
