import polars as pl

from datetime import datetime
from pathlib import Path
from time import sleep

from utils import *
from bell_alert import *
from google_calendar import *
from line_messaging import *


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "新刊通知リスト.xlsx"


def output_log(text: str) -> None:
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    print(f"{now} [INFO] {text}", flush=True)


def books_to_message(books: list) -> str:
    rows = [ {"title": b[0], "date": b[1]} for b in books ]

    df = (
        pl.DataFrame(rows)
        .group_by("date")
        .agg("title")
        .sort("date")
    )

    messages = []

    for row in df.iter_rows(named=True):
        release_date = row["date"]
        titles = "\n".join(sorted(row["title"]))

        messages.append(f"{release_date}\n{titles}")

    return "\n\n".join(messages)


if __name__ == "__main__":
    output_log("開始")
    today = datetime.now().strftime("%Y年%m月%d日")


    output_log("新刊通知リスト読み込み")
    book_db = load_db(DB_PATH)


    output_log("Google APIクライアント構築")
    service = build_api_cliant()


    output_log("新しい新刊情報の取得開始")

    books_add = []
    books_del = []

    for book in book_db:
        alert_id = book.alert_id
        category = book.category

        # 新刊情報の取得
        volume, release_date = extract_newbook_info(alert_id, category)
        sleep(1)

        # 新刊情報なし
        if volume is None and release_date is None:
            continue

        # カレンダー用タイトル
        if volume is None:
            calendar_title = f"{book.calendar_title} 新刊"
            volume = 0
        else:
            calendar_title = f"{book.calendar_title} {volume}"

        # 日付が異なる
        if release_date != book.release_date:

            # データベースの発売日に予定が残っていれば削除
            if is_registered(service, book.release_date, calendar_title):
                delete_event(
                    service,
                    book.release_date,
                    calendar_title
                )

                output_log(f"削除: {book.release_date} {calendar_title}")
                books_del.append((calendar_title, book.release_date))

            # 最新の新刊情報を登録
            if not is_registered(service, release_date, calendar_title):
                register_event(
                    service,
                    release_date,
                    calendar_title
                )

                output_log(f"追加: {release_date} {calendar_title}")

            book.volume = volume
            book.release_date = release_date

            books_add.append((calendar_title, release_date))

    # 更新
    save_db(book_db, DB_PATH)

    output_log("新しい新刊情報の取得完了")

    n_del = len(books_del)
    n_add = len(books_add)

    if n_del + n_add > 0:
        output_log("LINE通知")

        if n_del > 0:
            message_del = books_to_message(books_del)

            messages = [
                f"■カレンダーから削除（{n_del}件）",
                message_del
            ]

        else:
            messages = []

        if n_add > 0:
            message_add = books_to_message(books_add)

            messages += [
                f"■カレンダーに追加（{n_add}件）",
                message_add
            ]

        message = "\n\n".join(messages)
        send_line_message(message.strip())


    output_log("終了")
