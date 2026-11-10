
import os
import json
import requests
from pathlib import Path

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

API_URL = "https://api.bitget.com/api/v3/public/annoucements"
FEED_FILE = Path("bitget_feed.json")


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
    events = []

    # Monitor new coin listings and trading-pair delistings.
    for announcement_type in ("coin_listings", "symbol_delisting"):
        response = requests.get(
            API_URL,
            params={
                "language": "en_US",
                "annType": announcement_type,
                "limit": "10"
            },
            timeout=30
        )
        response.raise_for_status()

        result = response.json()

        if result.get("code") != "00000":
            raise RuntimeError(f"Bitget API error: {result}")

        for item in result.get("data", []):
            ann_id = item.get("annId")
            title = item.get("annTitle")
            link = item.get("annUrl")

            if ann_id and title and link:
                events.append({
                    "id": f"{announcement_type}_{ann_id}",
                    "title": title,
                    "url": link,
                    "type": announcement_type
                })

    return events


def load_seen():
    if not FEED_FILE.exists():
        return None

    try:
        data = json.loads(FEED_FILE.read_text(encoding="utf-8"))
        return set(data.get("seen_ids", []))
    except (json.JSONDecodeError, OSError):
        return None


def save_seen(seen_ids):
    FEED_FILE.write_text(
        json.dumps(
            {"seen_ids": sorted(seen_ids)},
            indent=2
        ),
        encoding="utf-8"
    )


def main():
    events = get_events()

    if not events:
        print("No Bitget announcements found.")
        return

    seen = load_seen()

    # First run: remember existing announcements without sending them.
    if seen is None or not seen:
        save_seen({event["id"] for event in events})
        print("First run complete. Existing Bitget announcements saved.")
        return

    new_events = [
        event for event in events
        if event["id"] not in seen
    ]

    if not new_events:
        print("No new Bitget announcements.")
        return

    for event in reversed(new_events):
        message = (
            "🚨 NEW BITGET EVENT\n\n"
            f"📢 {event['title']}\n\n"
            f"🔗 {event['url']}\n\n"
            "Source: Bitget"
        )

        send_telegram(message)
        seen.add(event["id"])
        save_seen(seen)
        print("Sent:", event["title"])


if __name__ == "__main__":
    main()
