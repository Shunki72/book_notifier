from datetime import datetime
from pathlib import Path
from time import sleep

from utils import *
from bell_alert import *
from google_calendar import *
from line_messaging import *


def output_log(text: str) -> None:
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    print(f"{now} [INFO] {text}", flush=True)


if __name__ == "__main__":
    output_log("開始")
    today = datetime.now().strftime("%Y年%m月%d日")


    output_log("新刊通知リスト読み込み")
    book_db = load_db()


    output_log("Google APIクライアント構築")
    service = build_api_cliant()


    output_log("新しい新刊情報の取得開始")

    messages_add = []
    messages_del = []

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
                messages_del.append((calendar_title, book.release_date))

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

            messages_add.append((calendar_title, release_date))

    # 更新
    save_db(book_db)

    output_log("新しい新刊情報の取得完了")


    if len(messages_add) + len(messages_del) > 0:
        output_log("LINE通知")

        n_del = len(messages_del)

        if n_del > 0:
            messages_del = sorted(messages_del, key=lambda x: x[1])
            messages_del = [ f"{date}\n{title}" for title, date in messages_del ]

            messages = [f"■カレンダーから削除（{n_del}件）"]
            messages += messages_del

        else:
            messages = []

        n_add = len(messages_add)

        if n_add > 0:
            messages_add = sorted(messages_add, key=lambda x: x[1])
            messages_add = [ f"{date}\n{title}" for title, date in messages_add ]

            messages += [f"■カレンダーに追加（{n_add}件）"]
            messages += messages_add

        message = "\n\n".join(messages)
        send_line_message(message.strip())


    output_log("終了")
