import os
import requests
from datetime import date

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DUFFEL_TOKEN = os.environ["DUFFEL_API_TOKEN"]

CHAT_ID = "569606874"  # твой Telegram ID

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text})

def check_flights():
    headers = {
       "Authorization": f"Bearer {DUFFEL_TOKEN}",
    "Duffel-Version": "v2",
    "Accept": "application/json",
    "Content-Type": "application/json",
    }

    payload = {
        "data": {
            "slices": [{
                "origin": "FRA",
                "destination": "DPS",
                "departure_date": date.today().replace(day=15).isoformat()
            }],
            "passengers": [
                {"type": "adult"},
                {"type": "adult"}
            ],
            "cabin_class": "business"
        }
    }

    r = requests.post(
        "https://api.duffel.com/air/offer_requests?return_offers=true",
        headers=headers,
        json=payload,
        timeout=30
    )
    if not r.ok:
        raise Exception(f"Duffel error {r.status_code}: {r.text}")

    offers = r.json()["data"]["offers"]

    if not offers:
        send_telegram("✈️ Бизнес-класс FRA → DPS не найден")
        return

    cheapest = min(offers, key=lambda o: float(o["total_amount"]))
    price = cheapest["total_amount"]
    currency = cheapest["total_currency"]

    send_telegram(
        "🔥 Найден бизнес-класс FRA → DPS\n"
        "💺 2 пассажира\n"
        f"💰 Цена: {price} {currency}"
    )

if __name__ == "__main__":
    check_flights()
