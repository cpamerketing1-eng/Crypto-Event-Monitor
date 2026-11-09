
import os
import json
import requests
from pathlib import Path

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

BINANCE_URL = (
    "https://www.binance.com/bapi/apex/v1/public/"
    "apex/cms/article/list/query"
)

FEED_FILE = Path("feed.json")


def get_events():
    params = {
        "type": 1,
        "pageNo": 1,
        "pageSize": 20
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        BINANCE_URL,
        params=params,
        headers=headers,
        timeout=30
    )
    response.raise_for_status()

    data = response.json()
    catalogs = data.get("data", {}).get("catalogs", [])

    events = []

    for catalog in catalogs:
        events.extend(catalog.get("articles", []))

    return events


def load_feed():
    if not FEED_FILE.exists():
        return None

    try:
        with open(FEED_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            codes = data.get("seen_codes", [])
            return set(str(code) for code in codes)

        return set()

    except (json.JSONDecodeError, OSError):
        return set()


def save_feed(seen_codes):
    data = {
        "seen_codes": list(seen_codes)[-1000:]
    }

    with open(FEED_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


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


def main():
    if not BOT_TOKEN or not CHANNEL_ID:
        raise RuntimeError(
            "BOT_TOKEN or CHANNEL_ID is missing!"
        )

    print("Checking Binance announcements...")

    events = get_events()

    if not events:
        print("No events found.")
        return

    seen_codes = load_feed()

    # First run: save existing events without sending old news.
    if seen_codes is None:
        seen_codes = set()

        for event in events:
            code = event.get("code")
            if code:
                seen_codes.add(str(code))

        save_feed(seen_codes)
        print("Initial event history saved.")
        print("New announcements will be sent from the next run.")
        return

    new_events = []

    for event in events:
        code = event.get("code")

        if not code:
            continue

        code = str(code)

        if code not in seen_codes:
            new_events.append(event)

    if not new_events:
        print("No new Binance events.")
        save_feed(seen_codes)
        return

    # Send older new events first.
    for event in reversed(new_events):
        code = str(event.get("code"))
        title = event.get("title", "New Binance Event")

        link = (
            "https://www.binance.com/en/support/announcement/"
            + code
        )

        message = (
            "🚨 NEW BINANCE EVENT\n\n"
            f"📢 {title}\n\n"
            f"🔗 {link}\n\n"
            "Source: Binance"
        )

        # Save only after successful delivery.
        send_telegram(message)
        seen_codes.add(code)

        save_feed(seen_codes)

        print(f"Sent successfully: {title}")

    print(f"Total new events sent: {len(new_events)}")


if __name__ == "__main__":
    main()
