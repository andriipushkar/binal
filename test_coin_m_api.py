import os
import json
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException

# --- Налаштування шляху до .env файлу ---
# Якщо test_coin_m_api.py знаходиться в папці pro1/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Припускаємо, що папка 'service' з '.env' знаходиться на тому ж рівні, що і 'balance'
# Якщо test_coin_m_api.py в pro1/, то шлях до service/.env буде 'service/.env'
# Якщо ви запускаєте з іншого місця, скоригуйте шлях відповідно.
SERVICE_DIR = os.path.join(SCRIPT_DIR, 'service') 
DOTENV_PATH = os.path.join(SERVICE_DIR, '.env')

# Альтернативно, якщо .env файл знаходиться в pro1/service, а test_coin_m_api.py в pro1/
# то DOTENV_PATH = os.path.join(SCRIPT_DIR, 'service', '.env')

# Якщо ви хочете жорстко задати шлях (наприклад, для тестування з будь-якої папки):
# DOTENV_PATH = 'D:/code/pro1/service/.env' # Замініть на ваш актуальний шлях

if not os.path.exists(DOTENV_PATH):
    print(f"Помилка: .env файл не знайдено за шляхом: {os.path.abspath(DOTENV_PATH)}")
    print("Будь ласка, перевірте змінну DOTENV_PATH у скрипті test_coin_m_api.py")
    exit()

# --- Завантаження API ключів ---
load_dotenv(dotenv_path=DOTENV_PATH)
api_key = os.environ.get('BINANCE_API_KEY')
secret_key = os.environ.get('BINANCE_SECRET_KEY')

if not api_key or not secret_key:
    print(f"Помилка: API ключі не завантажено з {DOTENV_PATH}.")
    print("Перевірте, чи встановлено змінні 'BINANCE_API_KEY' та 'BINANCE_SECRET_KEY' у файлі.")
    exit()

# --- Ініціалізація клієнта ---
try:
    client = Client(api_key, secret_key)
    client.ping() # Перевірка з'єднання
    print("Успішно підключено до Binance API.")
except BinanceAPIException as e:
    print(f"Помилка Binance API при ініціалізації клієнта: {e}")
    exit()
except Exception as e:
    print(f"Загальна помилка при ініціалізації клієнта: {e}")
    exit()


print("\nСпроба отримати інформацію про COIN-M ф'ючерсний акаунт...\n")

try:
    # --- СПРОБА 1: client.futures_coin_account() ---
    # Цей метод зазвичай повертає загальну інформацію про акаунт, 
    # включаючи список активів (assets) з їх балансами.
    print("--- Результат client.futures_coin_account() ---")
    coin_m_account_info = client.futures_coin_account() 
    print(json.dumps(coin_m_account_info, indent=4))
    print("-" * 50)

    if isinstance(coin_m_account_info, dict) and 'assets' in coin_m_account_info:
        print("\nЗнайдено ключ 'assets' у відповіді від futures_coin_account(). Приклади активів:")
        for asset_data in coin_m_account_info['assets'][:3]: # Перші три для прикладу
            print(json.dumps(asset_data, indent=4))
            asset_symbol = asset_data.get('asset')
            wallet_balance = asset_data.get('walletBalance')
            unrealized_pnl = asset_data.get('unrealizedProfit') 
            margin_balance = asset_data.get('marginBalance') # Також корисне поле
            
            print(f"  Актив: {asset_symbol}, Баланс гаманця: {wallet_balance}, "
                  f"Нереалізований PNL: {unrealized_pnl}, Маржинальний баланс: {margin_balance}")
    else:
        print("\nВідповідь від futures_coin_account() не містить ключа 'assets' або має іншу структуру.")


    # --- СПРОБА 2: client.futures_coin_balance() ---
    # Цей метод може повертати більш простий список балансів активів.
    # Розкоментуйте, щоб спробувати, якщо перший варіант не підійшов.
    # print("\n--- Результат client.futures_coin_balance() ---")
    # coin_m_balance_info = client.futures_coin_balance()
    # print(json.dumps(coin_m_balance_info, indent=4))
    # print("-" * 50)

    # if isinstance(coin_m_balance_info, list):
    #     print("\nВідповідь від futures_coin_balance() є списком. Приклади елементів:")
    #     for asset_data in coin_m_balance_info[:3]: # Перші три для прикладу
    #         print(json.dumps(asset_data, indent=4))
    #         asset_symbol = asset_data.get('asset')
    #         balance = asset_data.get('balance') # Може називатися 'balance'
    #         # PNL тут може бути відсутнім або бути в іншому полі
    #         print(f"  Актив: {asset_symbol}, Баланс: {balance}")
            

    # --- СПРОБА 3: client.futures_coin_account_balance() ---
    # Ще один варіант, який може мати дещо іншу структуру або набір даних
    # Розкоментуйте, щоб спробувати.
    # print("\n--- Результат client.futures_coin_account_balance() ---")
    # coin_m_acc_balance_info = client.futures_coin_account_balance() 
    # print(json.dumps(coin_m_acc_balance_info, indent=4))
    # print("-" * 50)

    # if isinstance(coin_m_acc_balance_info, list): # Часто баланси повертаються списком
    #     print("\nВідповідь від futures_coin_account_balance() є списком. Приклади елементів:")
    #     for item in coin_m_acc_balance_info[:3]:
    #         print(json.dumps(item, indent=4))
            # Шукайте тут 'asset', 'balance', 'walletBalance', 'unrealizedProfit' і т.д.

except BinanceAPIException as e:
    print(f"Помилка Binance API: {e}")
    if e.code == -2015: # Invalid API-key, IP, or permissions for action.
        print("ПОРАДА: Перевірте дозволи API ключа для ф'ючерсної торгівлі (COIN-M).")
except Exception as e:
    print(f"Загальна помилка: {e}")