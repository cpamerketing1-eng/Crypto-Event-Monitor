
import requests
import time
from datetime import datetime

URL = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"

seen_events = set()

def check_events():
    try:
        response = requests.get(
            URL,
            params={"type": 1, "pageNo": 1, "pageSize": 10},
            timeout=15
        )

        response.raise_for_status()
        data = response.json()

        articles = data.get("data", {}).get("articles", [])

        for article in articles:
            title = article.get("title", "")
            code = article.get("code", "")

            if not title or not code:
                continue

            if code not in seen_events:
                seen_events.add(code)

                message = (
                    "🚨 BINANCE NEW ANNOUNCEMENT\n\n"
                    f"📌 {title}\n\n"
                    f"🔗 https://www.binance.com/en/support/announcement/{code}\n\n"
                    f"🕒 {datetime.now()}"
                )

                print(message)

    except Exception as error:
        print("Error:", error)


if __name__ == "__main__":
    print("Crypto Event Monitor Started!")
    while True:
        check_events()
        time.sleep(60)
