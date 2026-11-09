
import os
import json
import requests
from pathlib import Path

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

API_URL = "https://www.binance.com/bapi/apex/v1/public/apex/cms/article/list/query"

FEED_FILE = Path("feed.json")


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHANNEL_ID,
            "text": message,
            "disable_web_page_preview": True
        },
        timeout=30
    )

    response.raise_for_status()

    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegram error: {result}")


def get_events():
    response = requests.get(
        API_URL,
        params={
            "type": 1,
            "pageNo": 1,
            "pageSize": 20
        },
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=30
    )

    response.raise_for_status()
    data = response.json()

    catalogs = data.get("data", {}).get("catalogs", [])
    events = []

    for catalog in catalogs:
        for article in catalog.get("articles", []):
            code = article.get("code")
            title = article.get("title")

            if code and title:
                events.append({
                    "code": str(code),
                    "title": title,
                    "url": (
                        "https://www.binance.com/en/support/announcement/"
                        + str(code)
                    )
                })

    return events


def load_seen():
    if not FEED_FILE.exists():
        return None

    try:
        data = json.loads(FEED_FILE.read_text(encoding="utf-8"))
        return set(data.get("seen_codes", []))
    except (json.JSONDecodeError, OSError):
        return None


def save_seen(seen_codes):
    FEED_FILE.write_text(
        json.dumps(
            {"seen_codes": sorted(seen_codes)},
            indent=2
        ),
        encoding="utf-8"
    )


def main():
    events = get_events()

    if not events:
        print("No events found.")
        return

    seen = load_seen()

    # First run: save existing events without sending old notifications.
    if seen is None or not seen:
        save_seen({event["code"] for event in events})
        print("First run complete. Existing events saved; no old messages sent.")
        return

    new_events = [
        event for event in events
        if event["code"] not in seen
    ]

    if not new_events:
        print("No new Binance events.")
        return

    # Send each new event once.
    for event in reversed(new_events):
        message = (
            "🚨 NEW BINANCE EVENT\n\n"
            f"📢 {event['title']}\n\n"
            f"🔗 {event['url']}\n\n"
            "Source: Binance"
        )

        send_telegram(message)
        seen.add(event["code"])
        save_seen(seen)
        print("Sent:", event["title"])


if __name__ == "__main__":
    main()
