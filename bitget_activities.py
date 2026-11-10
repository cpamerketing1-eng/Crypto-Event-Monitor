
import os
import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

PAGE_URL = "https://www.bitget.com/support/sections/4413154768537"
FEED_FILE = Path("bitget_activities_feed.json")


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
        raise RuntimeError(result)


def get_activities():
    response = requests.get(
        PAGE_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    activities = {}

    for link in soup.find_all("a", href=True):
        href = link["href"]
        title = link.get_text(" ", strip=True)

        if "/support/articles/" not in href or not title:
            continue

        full_url = requests.compat.urljoin(PAGE_URL, href)
        activities[full_url] = {
            "title": title,
            "url": full_url
        }

    return list(activities.values())


def main():
    activities = get_activities()

    if not activities:
        raise RuntimeError(
            "No activities found. Bitget page structure may have changed."
        )

    if FEED_FILE.exists():
        seen = set(json.loads(FEED_FILE.read_text(encoding="utf-8")))
    else:
        seen = set()

    if not seen:
        seen = {item["url"] for item in activities}
        FEED_FILE.write_text(
            json.dumps(sorted(seen), indent=2),
            encoding="utf-8"
        )
        print("First run: existing activities saved.")
        return

    new_items = [
        item for item in reversed(activities)
        if item["url"] not in seen
    ]

    for item in new_items:
        message = (
            "🎁 NEW BITGET ACTIVITY\n\n"
            f"📢 {item['title']}\n\n"
            f"🔗 {item['url']}\n\n"
            "Source: Bitget"
        )

        send_telegram(message)
        seen.add(item["url"])
        FEED_FILE.write_text(
            json.dumps(sorted(seen), indent=2),
            encoding="utf-8"
        )
        print("Sent:", item["title"])

    if not new_items:
        print("No new Bitget activities.")


if __name__ == "__main__":
    main()
