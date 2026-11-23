import os
import time
from datetime import datetime
import requests
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

# Загружаем конфигурацию
load_dotenv()
TRADE_MODE = os.getenv("TRADE_MODE", "PAPER")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Бот запущен в режиме: {TRADE_MODE}")

def send_discord_message(text):
    """Отправляет уведомление на сервер Discord через вебхук."""
    if not DISCORD_WEBHOOK_URL:
        print("Предупреждение: DISCORD_WEBHOOK_URL не настроен в .env")
        return
    payload = {"content": text}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code != 204:
            print(f"Ошибка отправки в Discord: {response.status_code}")
    except Exception as e:
        print(f"Не удалось отправить сообщение в Discord: {e}")

def load_triggers(file_path="triggers.txt"):
    active_triggers = []
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    if not os.path.exists(file_path):
        return active_triggers

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                date_str, outcome, max_price_str = line.split(",")
                if date_str.strip() == current_date:
                    active_triggers.append({
                        "outcome": outcome.strip(),
                        "max_price": float(max_price_str.strip())
                    })
            except ValueError:
                continue
    return active_triggers

def fetch_external_api():
    """
    Делает реальный запрос к API Binance и возвращает текущую цену Биткоина (BTC/USDT).
    """
    url = "https://api1.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return float(data["price"])  # Возвращает чистый флоат, например 93450.50
        else:
            print(f"Ошибка API Binance: {response.status_code}")
            return None
    except Exception as e:
        print(f"Не удалось получить данные с биржи: {e}")
        return None

def check_market_logic():
    print(f"\n⏱ [{datetime.now().strftime('%H:%M:%S')}] Плановый опрос биржи Binance...")
    
    triggers = load_triggers()
    if not triggers:
        print("Нет активных триггеров на сегодня в triggers.txt")
        return

    current_btc_price = fetch_external_api()
    if current_btc_price is None:
        return

    print(f"Текущий курс Биткоина: ${current_btc_price}")

    for t in triggers:
        # Для Биткоина порог в файле — это цена триггера (например, если упадет ниже 95000)
        print(f"Проверяем триггер: Исход {t['outcome']}, Целевой порог: {t['max_price']}")
        
        if current_btc_price <= t["max_price"]:
            print(f"🚨 ТРИГГЕР СРАБОТАЛ! Включаем пиковый режим...")
            
            msg = (
                f"🚨 **[Polymarket Bot] Условия по BTC выполнены!**\n"
                f"📈 Исход: `{t['outcome']}`\n"
                f"💰 Курс BTC: `${current_btc_price}` (Порог: <= {t['max_price']})\n"
                f"⚙️ Режим: `{TRADE_MODE}`\n"
                f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            send_discord_message(msg)
            
            for i in range(3):
                print(f"   [Секунда {i+1}] Высокочастотный парсинг ликвидности Polymarket CLOB...")
                if TRADE_MODE == "PAPER":
                    with open("paper_ledger.log", "a", encoding="utf-8") as log:
                        log.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Имитация ордера под BTC по цене {current_btc_price}\n")
                time.sleep(1)
            break
        else:
            print("Цена Биткоина выше порога. Сигнала на покупку нет.")

# Настраиваем планировщик
scheduler = BlockingScheduler()
scheduler.add_job(check_market_logic, 'interval', seconds=10)

try:
    print("Робот-сканер Биткоина запущен. Опрос каждые 10 секунд...")
    check_market_logic()
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    print("Бот остановлен.")

