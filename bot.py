import os
import random
import time
from datetime import datetime
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

# Загружаем конфигурацию
load_dotenv()
TRADE_MODE = os.getenv("TRADE_MODE", "PAPER")

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Бот запущен в режиме: {TRADE_MODE}")

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
    Имитация внешнего API. Возвращает числовое значение.
    (В реальном проекте здесь будет requests.get() к нужному сайту)
    """
    # Генерируем случайную цену от 0.50 до 0.80
    mock_price = round(random.uniform(0.50, 0.80), 2)
    return mock_price

def check_market_logic():
    """
    Основная логика, которая запускается по расписанию.
    """
    print(f"\n⏱ [{datetime.now().strftime('%H:%M:%S')}] Плановый опрос внешнего API...")
    
    triggers = load_triggers()
    if not triggers:
        print("Нет активных триггеров на сегодня.")
        return

    # Получаем текущее числовое значение от внешнего API
    current_api_value = fetch_external_api()
    print(f"Значение с внешнего API: {current_api_value}")

    for t in triggers:
        print(f"Проверяем триггер: Исход {t['outcome']}, Порог: {t['max_price']}")
        
        # Если значение с API упало ниже или равно нашему порогу
        if current_api_value <= t["max_price"]:
            print(f"🚨 ТРИГГЕР СРАБОТАЛ! Включаем пиковый режим (опрос каждую секунду)...")
            
            # Пиковый режим: опрашиваем стакан 5 раз подряд с интервалом в 1 секунду
            for i in range(5):
                print(f"   [Секунда {i+1}] Запрос в стакан через py-clob-client (Проверка ликвидности)...")
                
                if TRADE_MODE == "PAPER":
                    print(f"   ⚡ [PAPER] Запись в лог: Купил бы {t['outcome']} по цене {current_api_value}")
                    with open("paper_ledger.log", "a", encoding="utf-8") as log:
                        log.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Имитация ордера: {t['outcome']} по цене {current_api_value}\n")
                
                time.sleep(1) # Задержка в 1 секунду между пиковыми запросами
            break
        else:
            print("Условия не выполнены. Ждем следующего планового интервала.")

# Настраиваем планировщик APScheduler
scheduler = BlockingScheduler()

# Запускаем проверку каждые 10 секунд для наглядности тестов
# (Заказчик просил конкретные минуты часа, для этого в проде ставится trigger='cron', minute='*/5')
scheduler.add_job(check_market_logic, 'interval', seconds=10)

try:
    print("Планировщик запущен. Опрос происходит каждые 10 секунд. Нажмите Ctrl+C для выхода.")
    check_market_logic() # Первый запуск сразу при старте
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    print("Бот остановлен.")
