from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

from utils import retry


# ログイン情報
BASE_DIR = Path(__file__).resolve().parent.parent
GOOGLE_DIR = BASE_DIR / "google"

GOOGLE_CREDENTIALS_PATH = GOOGLE_DIR / "credentials.json"
GOOGLE_TOKEN_PATH = GOOGLE_DIR / "token.json"


# 権限
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def build_api_cliant() -> Resource:
    """
    APIクライアントを構築する。
    """
    # 認証
    if GOOGLE_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_PATH, SCOPES)

    else:
        flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)

        with GOOGLE_TOKEN_PATH.open("w") as f:
            f.write(creds.to_json())

    # APIクライアント構築
    return build('calendar', 'v3', credentials=creds)


@retry(n_retry=10)
def is_registered(
        service: Resource,
        date_str: str,
        title: str,
        calendar_id: str = "primary",
        timezone: str = "Asia/Tokyo"
    ) -> bool:
    """
    与えられた日付に、与えられたタイトルの予定が登録済みかどうか判定する。
    """
    # 日付の設定
    target_date = datetime.strptime(date_str, "%Y年%m月%d日").date()

    # タイムゾーンの設定
    tz = ZoneInfo(timezone)

    # 開始日時（当日0時）
    time_min = datetime.combine(
        target_date,
        datetime.min.time(),
        tzinfo = tz
    )

    # 終了日時（翌日0時）
    time_max = time_min + timedelta(days=1)

    # 予定の取得
    page_token = None

    while True:
        response = (
            service
            .events()
            .list(
                calendarId = calendar_id,
                timeMin = time_min.isoformat(),
                timeMax = time_max.isoformat(),
                singleEvents = True,
                showDeleted = False,
                pageToken = page_token
            )
            .execute()
        )

        for event in response.get("items", []):
            event_title = event.get("summary", "").strip()

            # 登録済み
            if event_title == title:
                return True

        page_token = response.get("nextPageToken")

        if page_token is None:
            break

    return False


@retry(n_retry=10)
def register_event(
        service: Resource,
        date_str: str,
        title: str,
        calendar_id: str = "primary",
        color_id: str = "5"
    ) -> None:
    """
    カレンダーに予定を追加する。
    """
    # 開始日（当日0時）
    start_date = datetime.strptime(date_str, "%Y年%m月%d日").date()

    # 終了日（翌日0時）
    end_date = start_date + timedelta(days=1)

    # 登録する予定情報
    event_body = {
        "summary": title.strip(),
        "start": {
            "date": start_date.isoformat()
        },
        "end": {
            "date": end_date.isoformat()
        },
        "colorId": color_id
    }

    # 登録
    registered_event = (
        service
        .events()
        .insert(
            calendarId = calendar_id,
            body = event_body
        )
        .execute()
    )


@retry(n_retry=10)
def delete_event(
        service: Resource,
        date_str: str,
        title: str,
        calendar_id: str = "primary",
        timezone: str = "Asia/Tokyo"
    ) -> None:
    """
    与えられた日付とタイトルに一致する予定を削除する。
    """
    # 日付の設定
    target_date = datetime.strptime(date_str, "%Y年%m月%d日").date()

    # タイムゾーンの設定
    tz = ZoneInfo(timezone)

    # 開始日時（当日0時）
    time_min = datetime.combine(
        target_date,
        datetime.min.time(),
        tzinfo = tz
    )

    # 終了日時（翌日0時）
    time_max = time_min + timedelta(days=1)

    # 予定の取得
    page_token = None

    while True:
        response = (
            service
            .events()
            .list(
                calendarId = calendar_id,
                timeMin = time_min.isoformat(),
                timeMax = time_max.isoformat(),
                singleEvents = True,
                showDeleted = False,
                pageToken = page_token
            )
            .execute()
        )

        for event in response.get("items", []):
            event_title = event.get("summary", "").strip()

            # タイトルが異なる
            if event_title != title:
                continue

            event_id = event.get("id")

            if not event_id:
                continue

            # 当該イベント削除
            (
                service
                .events()
                .delete(
                    calendarId = calendar_id,
                    eventId = event_id,
                    sendUpdates = "none"
                )
                .execute()
            )

        page_token = response.get("nextPageToken")

        if page_token is None:
            break
