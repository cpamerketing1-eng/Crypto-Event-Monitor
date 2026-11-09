import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

BINANCE_URL = "https://www.binance.com/bapi/apex/v1/public/apex/cms/article/list/query"


def get_events():

    params = {
        "type": 1,
        "pageNo": 1,
        "pageSize": 10
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        BINANCE_URL,
        params=params,
        headers=headers,
        timeout=25
    )

    response.raise_for_status()

    data = response.json()

    catalogs = data.get("data", {}).get("catalogs", [])

    events = []

    for catalog in catalogs:
        for article in catalog.get("articles", []):
            events.append(article)

    return events


def send_telegram(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHANNEL_ID,
            "text": message,
            "disable_web_page_preview": True
        },
        timeout=20
    )

    response.raise_for_status()

    print("Telegram notification sent!")


if __name__ == "__main__":

    if not BOT_TOKEN or not CHANNEL_ID:
        print("ERROR: BOT_TOKEN or CHANNEL_ID missing in .env")

    else:
        try:
            events = get_events()

            if events:

                event = events[0]

                title = event.get("title", "New Binance Event")
                code = event.get("code", "")

                link = f"https://www.binance.com/en/support/announcement/{code}"

                message = (
                    "🚨 NEW BINANCE EVENT\n\n"
                    f"📢 {title}\n\n"
                    f"🔗 {link}\n\n"
                    "Source: Binance"
                )

                send_telegram(message)

            else:
                print("No events found")

        except Exception as e:
            print("ERROR:", e)