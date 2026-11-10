# Telegram Bitget Channel Watcher

Checks the five public Telegram channels every 5 minutes and sends new posts containing `bitget.com` links to the destination configured by your existing `CHANNEL_ID` GitHub secret.

## Important
- Your personal Telegram account must join all five source channels.
- The bot does **not** need to be an admin in those source channels.
- This uses a Telethon user session. Keep `TG_SESSION_STRING` private. Never paste it into chat or commit it to GitHub.
- First run only saves the latest message IDs. It does not forward old posts.
- GitHub Actions scheduled jobs are not guaranteed to start at the exact minute.
- This forwards the post text and Bitget links, not the original media/file.

## Files
- `telegram_bitget_watcher.py`: watcher
- `.github/workflows/telegram_bitget_watcher.yml`: scheduled GitHub Actions workflow

## GitHub Secrets to add
Keep your existing `BOT_TOKEN` and `CHANNEL_ID` secrets. Add:
- `TG_API_ID`
- `TG_API_HASH`
- `TG_SESSION_STRING`

Get API ID and API Hash at https://my.telegram.org (API Development Tools).

Generate a Telethon StringSession on your own computer using the official Telethon documentation. The session string gives access to your Telegram account, so treat it like a password. Do not share it with anyone.

## Setup
1. Upload `telegram_bitget_watcher.py` to the repository root.
2. Upload `.github/workflows/telegram_bitget_watcher.yml` to the same folder path in the repository.
3. Add the three new GitHub Actions secrets listed above.
4. Run the workflow once manually from Actions. It will establish a baseline; it will not send old messages.
5. Later new posts containing Bitget URLs will be sent to your existing `CHANNEL_ID` destination.
