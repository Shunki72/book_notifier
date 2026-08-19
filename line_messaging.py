import json

from pathlib import Path
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)

from utils import retry


BASE_DIR = Path(__file__).resolve().parent.parent
LINE_DIR = BASE_DIR / "line"

LINE_TOKEN_PATH = LINE_DIR / "token.json"


@retry(n_retry=10)
def send_line_message(text: str) -> None:
    """
    LINEメッセージを送る。
    """
    # トークンの取得
    with LINE_TOKEN_PATH.open("r") as f:
        data = json.load(f)

    USER_ID = data["user_id"]
    CHANNEL_ACCESS_TOKEN = data["channel_access_token"]

    config = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

    with ApiClient(config) as api_cliant:
        api = MessagingApi(api_cliant)

        api.push_message(
            PushMessageRequest(
                to=USER_ID,
                messages=[
                    TextMessage(text=text)
                ]
            )
        )
