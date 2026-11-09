import requests

URL = "https://www.binance.com/bapi/apex/v1/public/apex/cms/article/list/query"

params = {
    "type": 1,
    "pageNo": 1,
    "pageSize": 10
}

headers = {
    "User-Agent": "Mozilla/5.0"
}

try:
    response = requests.get(
        URL,
        params=params,
        headers=headers,
        timeout=25
    )

    response.raise_for_status()

    data = response.json()

    catalogs = data.get("data", {}).get("catalogs", [])

    if catalogs:
        articles = catalogs[0].get("articles", [])

        print("\n===== BINANCE LATEST EVENTS =====\n")

        for article in articles:
            print("Title:", article.get("title"))
            print("Code:", article.get("code"))
            print("-----------------------------")

        print("\nTotal Events:", len(articles))

    else:
        print("No events found")

except Exception as e:
    print("Error:", e)