import json
import os
import re
import time
from pathlib import Path

import requests
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageEntityTextUrl

CHANNELS = [
    "bitgetcn_announcement",
    "echphaisinh",
    "BitgetAnunciosPTBR",
    "TraderOmerPublic",
    "BestearningofferBD",
]
STATE_FILE = Path("telegram_channels_state.json")
BITGET_RE = re.compile(r"(?i)(?:https?://)?(?:www\.)?bitget\.com(?:[/:?#]|$)")

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def get_message_text_and_urls(message):
    text = message.message or ""
    urls = set(BITGET_RE.findall(text))
    # Also inspect hidden text-URL entities, where the URL is not visible in the text.
    for entity in (message.entities or []):
        if isinstance(entity, MessageEntityTextUrl):
            url = entity.url or ""
            if "bitget.com" in url.lower():
                urls.add(url)
    return text, sorted(urls)

def send_to_target(bot_token, target_chat_id, message_text, urls, source):
    lines = [f"📢 Bitget link detected", f"Source: {source}"]
    if message_text.strip():
        lines.extend(["", message_text.strip()])
    # Include hidden URLs too, and ensure visible Bitget URLs are present.
    for url in urls:
        if url not in message_text:
            lines.append(url)
    payload = {
        "chat_id": target_chat_id,
        "text": "\n".join(lines)[:4000],
        "disable_web_page_preview": False,
    }
    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegram Bot API error: {result}")

def main():
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]
    session_string = os.environ["TG_SESSION_STRING"]
    bot_token = os.environ["BOT_TOKEN"]
    target_chat_id = os.environ["CHANNEL_ID"]

    state = load_state()
    client = TelegramClient(StringSession(session_string), api_id, api_hash)

    async def run():
        await client.start()
        for username in CHANNELS:
            try:
                entity = await client.get_entity(username)
                key = username.lower()
                last_id = int(state.get(key, 0))

                # First run: save the latest post ID only; do not forward old posts.
                if key not in state:
                    latest = await client.get_messages(entity, limit=1)
                    state[key] = latest[0].id if latest else 0
                    print(f"Baseline saved for @{username}: {state[key]}")
                    continue

                new_messages = []
                async for msg in client.iter_messages(
                    entity, min_id=last_id, reverse=True, limit=100
                ):
                    new_messages.append(msg)

                for msg in new_messages:
                    text, urls = get_message_text_and_urls(msg)
                    if "bitget.com" in text.lower() or urls:
                        send_to_target(
                            bot_token, target_chat_id, text, urls, f"@{username}"
                        )
                        print(f"Forwarded @{username} message {msg.id}")
                    state[key] = max(int(state.get(key, 0)), msg.id)
                print(f"Checked @{username}; latest saved ID: {state[key]}")
            except Exception as exc:
                print(f"Problem checking @{username}: {exc}")
                raise
        save_state(state)
        await client.disconnect()

    with client:
        client.loop.run_until_complete(run())

if __name__ == "__main__":
    main()
