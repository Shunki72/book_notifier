import re
import requests

from bs4 import BeautifulSoup

from utils import retry


# ベルアラートのURL
BELL_ALERT_URL = "https://alert.shop-bell.com/"

# カテゴリー別のパス
CATEGORY_PATH = {
    "漫画": "comic/",
    "ラノベ": "ranobe/detail/",
    "電子書籍": "comic/ebook/"
}


def set_bell_alert_url(alert_id: int, category: str) -> str:
    """
    与えられたアラートIDのURLを返す。
    """
    return BELL_ALERT_URL + CATEGORY_PATH[category] + str(alert_id)


@retry(n_retry=10)
def extract_newbook_info(alert_id: int, category: str) -> tuple:
    """
    アラートIDのURLから最新刊に関する情報を取得する。
    """
    url = set_bell_alert_url(alert_id, category)

    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    lead = soup.find("div", class_="iteminfo lead").text.strip()

    # 次巻の巻数と発売予定日が取得できるかどうか
    pattern = r"(\d+)巻は(\d{4}年\d{2}月\d{2}日)の発売予定です。"
    result = re.search(pattern, lead)

    if result:
        volume = int(result.group(1))
        release_date = result.group(2)
        return volume, release_date

    # 次巻の発売予定日が取得できるかどうか
    pattern = r"次巻は(\d{4}年\d{2}月\d{2}日)の発売予定です。"
    result = re.search(pattern, lead)

    if result:
        release_date = result.group(1)
        return None, release_date

    # 次巻の巻数と発売予定日が取得できなかった場合
    return None, None
