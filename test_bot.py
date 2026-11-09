import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("BOT_TOKEN")
channel = os.getenv("CHANNEL_ID")

url = f"https://api.telegram.org/bot{token}/sendMessage"

response = requests.post(url, data={
    "chat_id": channel,
    "text": "✅ Crypto Event Monitor Bot Connected Successfully!"
})

print(response.status_code)
print(response.text)