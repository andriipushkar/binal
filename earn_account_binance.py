import os
import logging
from datetime import datetime
import json # Потрібен для підготовки даних для JSON

# Імпортуємо лише необхідні функції з нашого пакета 'balance'
# load_api_keys, initialize_binance_client, get_earn_balance з balance.api
# save_to_json, save_to_txt з balance.data_processing
from balance.api import load_api_keys, initialize_binance_client, get_earn_balance
from balance.data_processing import save_to_json, save_to_txt

# --- Визначення шляхів відносно директорії цього скрипта (earn_account_binance.py) ---
# earn_account_binance.py знаходиться в pro1/
SCRIPT_DIR = os.path.dirname(__file__)
# Папка service знаходиться поруч з цим скриптом
SERVICE_DIR = os.path.join(SCRIPT_DIR, 'service')
DOTENV_PATH = os.path.join(SERVICE_DIR, '.env')

# Папки logs та output знаходяться всередині папки balance/
LOG_DIR = os.path.join(SCRIPT_DIR, 'balance', 'logs') # Логи для цього скрипта тут
# Якщо хочеш окрему папку логів для цього скрита, зміни рядок вище на:
# LOG_DIR = os.path.join(SCRIPT_DIR, 'logs_earn') # Створиться папка logs_earn в pro1/

OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'balance', 'output') # Вихідні файли для цього скрита тут


# --- Налаштування логування (робимо це тут, в точці входу) ---
# Перевіряємо та створюємо папку logs (або logs_earn), якщо її немає
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Формат імені файлу логу:YYYY-MM-DD_HH-MM-SS_earn.log (для розрізнення логів)
log_file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '_earn.log'
log_file_path = os.path.join(LOG_DIR, log_file_name)

# Налаштовуємо базову конфігурацію логування лише один раз
if not logging.root.handlers:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(log_file_path, encoding='utf-8'),
                            logging.StreamHandler() # Вивід у консоль
                        ])

# --- Головна логіка виконання цього скрипта ---
def main():
    logging.info("Розпочато виконання скрипта earn_account_binance.py")

    # 1. Завантаження API ключів
    api_key, secret_key = load_api_keys(dotenv_file_path=DOTENV_PATH)
    if not api_key or not secret_key:
        return

    # 2. Ініціалізація клієнта Binance API
    binance_client = initialize_binance_client(api_key, secret_key)
    if not binance_client:
        return

    logging.info("\nОтримання Earn балансу...")

    # 3. Отримання тільки Earn балансу (використовуємо функцію з модуля balance.api)
    earn_list, total_earn_usd = get_earn_balance(binance_client)
    logging.info(f"\nЗагальний Binance Earn баланс (оцінка в USD): {total_earn_usd:.2f} USD")

    # Ми не отримуємо спотовий чи ф'ючерсний баланс тут.

    # 4. Підготовка даних для збереження (тільки Earn баланс)
    current_time = datetime.now()
    earn_data_to_save_json = {
        'timestamp': current_time.isoformat(),
        'earn_balance': { # Використовуємо ту саму структуру, що і в main.py
             'total_estimated_usd': total_earn_usd,
             'assets': earn_list # Список активів Earn
        }
        # Не включаємо інші баланси тут
    }

    # Підготовка даних для TXT файлу
    earn_data_to_save_txt = f"Звіт про Binance Earn баланс станом на: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    earn_data_to_save_txt += "="*40 + "\n\n"
    earn_data_to_save_txt += "--- Binance Earn рахунок ---\n"
    if earn_list:
         # Форматуємо дані Earn для TXT вручну, аналогічно до ф'ючерсів
         for item in earn_list:
              earn_data_to_save_txt += f"  {item['Актив']} ({item.get('Продукт', 'Earn')}): {item['Всього']:.8f}"
              if item.get('Вартість (USD)') is not None:
                  earn_data_to_save_txt += f" (~{item['Вартість (USD)']:.2f} USD)"
              earn_data_to_save_txt += "\n"
    else:
         earn_data_to_save_txt += "На рахунку Binance Earn немає активів з балансом > 0 (або не знайдено підтримуваних продуктів).\n"

    earn_data_to_save_txt += f"\nЗагальний Binance Earn баланс (оцінка в USD): {total_earn_usd:.2f} USD\n"
    earn_data_to_save_txt += "="*40 + "\n"


    # 5. Збереження даних у файли (використовуємо функції з balance.data_processing, передаємо шлях та імена файлів)
    json_output_file_name = 'earn_account_binance_output.json' # Нове ім'я для Earn JSON
    txt_output_file_name = 'earn_account_binance_output.txt' # Нове ім'я для Earn TXT

    save_to_json(earn_data_to_save_json, output_dir_path=OUTPUT_DIR, file_name=json_output_file_name)
    save_to_txt(earn_data_to_save_txt, output_dir_path=OUTPUT_DIR, file_name=txt_output_file_name)


    logging.info("\nВиконання скрипта earn_account_binance.py завершено.")

# Точка входу при прямому запуску файлу
if __name__ == "__main__":
    main()