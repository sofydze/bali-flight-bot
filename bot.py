import os
import requests
from datetime import date, timedelta


TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DUFFEL_TOKEN = os.environ["DUFFEL_API_TOKEN"]

# Твой Telegram chat_id (как на скрине)
CHAT_ID = "569606874"

# Маршрут
ORIGIN = "FRA"
DESTINATION = "DPS"

# Пассажиры
PASSENGERS = 2

# Класс
CABIN_CLASS = "business"  # economy / premium_economy / business / first


def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=30)


def pick_departure_date() -> str:
    """
    Безопасная дата: ставим 15-е число текущего месяца.
    Если сегодня уже после 15-го — берем 15-е следующего месяца.
    """
    today = date.today()
    if today.day <= 15:
        dep = today.replace(day=15)
    else:
        # переходим в следующий месяц
        first_next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        dep = first_next_month.replace(day=15)
    return dep.isoformat()


def check_flights() -> None:
    headers = {
        "Authorization": f"Bearer {DUFFEL_TOKEN}",
        "Duffel-Version": "v2",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = {
        "data": {
            "slices": [
                {
                    "origin": ORIGIN,
                    "destination": DESTINATION,
                    "departure_date": pick_departure_date(),
                }
            ],
            "passengers": [{"type": "adult"} for _ in range(PASSENGERS)],
            "cabin_class": CABIN_CLASS,
        }
    }

    r = requests.post(
        "https://api.duffel.com/air/offer_requests?return_offers=true",
        headers=headers,
        json=payload,
        timeout=30,
    )

    # Вместо падения — отправляем подробную ошибку в Telegram и выходим
    if not r.ok:
        send_telegram(
            "❌ Duffel API error\n"
            f"Status: {r.status_code}\n"
            f"Response: {r.text}"
        )
        return

    data = r.json().get("data", {})
    offers = data.get("offers", []) or []

    if not offers:
        send_telegram(f"✈️ {CABIN_CLASS.upper()} {ORIGIN} → {DESTINATION}: офферы не найдены")
        return

    # Ищем самый дешевый оффер
    def offer_price(o):
        try:
            return float(o.get("total_amount", "inf"))
        except Exception:
            return float("inf")

    cheapest = min(offers, key=offer_price)
    price = cheapest.get("total_amount")
    currency = cheapest.get("total_currency")
    dep_date = payload["data"]["slices"][0]["departure_date"]

    send_telegram(
        f"🔥 Найден {CABIN_CLASS.upper()} {ORIGIN} → {DESTINATION}\n"
        f"📅 Дата: {dep_date}\n"
        f"👤 Пассажиров: {PASSENGERS}\n"
        f"💰 Цена: {price} {currency}"
    )


if __name__ == "__main__":
    check_flights()
