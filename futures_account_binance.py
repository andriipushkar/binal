import os
import logging
from datetime import datetime
import json # Потрібен для підготовки даних для JSON

# Імпортуємо лише необхідні функції з нашого пакета 'balance'
# load_api_keys, initialize_binance_client, get_futures_balance з balance.api
# save_to_json, save_to_txt з balance.data_processing
from balance.api import load_api_keys, initialize_binance_client, get_futures_balance
from balance.data_processing import save_to_json, save_to_txt

# --- Визначення шляхів відносно директорії цього скрипта (futures_account_binance.py) ---
# futures_account_binance.py знаходиться в pro1/
SCRIPT_DIR = os.path.dirname(__file__)
# Папка service знаходиться поруч з цим скриптом
SERVICE_DIR = os.path.join(SCRIPT_DIR, 'service')
DOTENV_PATH = os.path.join(SERVICE_DIR, '.env')

# Папки logs та output знаходяться всередині папки balance/
LOG_DIR = os.path.join(SCRIPT_DIR, 'balance', 'logs') # Логи для цього скрипта тут
# Якщо хочеш окрему папку логів для цього скрипта, зміни рядок вище на:
# LOG_DIR = os.path.join(SCRIPT_DIR, 'logs_futures') # Створиться папка logs_futures в pro1/

OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'balance', 'output') # Вихідні файли для цього скрипта тут


# --- Налаштування логування (робимо це тут, в точці входу) ---
# Перевіряємо та створюємо папку logs (або logs_futures), якщо її немає
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Формат імені файлу логу:<\ctrl97>code]YYYY-MM-DD_HH-MM-SS_futures.log[/%code] (для розрізнення логів)
log_file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '_futures.log'
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
    logging.info("Розпочато виконання скрипта futures_account_binance.py")

    # 1. Завантаження API ключів
    api_key, secret_key = load_api_keys(dotenv_file_path=DOTENV_PATH)
    if not api_key or not secret_key:
        return

    # 2. Ініціалізація клієнта Binance API
    binance_client = initialize_binance_client(api_key, secret_key)
    if not binance_client:
        return

    logging.info("\nОтримання ф'ючерсного балансу...")

    # 3. Отримання тільки ф'ючерсного балансу (використовуємо функцію з модуля balance.api)
    total_futures_usdt, futures_usdt_info = get_futures_balance(binance_client)
    futures_balance_usd = total_futures_usdt # Для USDT-M ф'ючерсів оцінка в USD = баланс в USDT
    logging.info(f"\nЗагальний ф'ючерсний баланс (оцінка в USD): {futures_balance_usd:.2f} USD")

    # Ми не отримуємо спотовий баланс і не форматуємо таблицю тут.

    # 4. Підготовка даних для збереження (тільки ф'ючерсний баланс)
    current_time = datetime.now()
    futures_data_to_save_json = {
        'timestamp': current_time.isoformat(),
        'futures_balance_usdt_m': futures_usdt_info # Використовуємо дані USDT ф'ючерсів
        # Не включаємо спотовий баланс та загальний підсумок тут
    }

    # Підготовка даних для TXT файлу
    futures_data_to_save_txt = f"Звіт про ф'ючерсний баланс Binance (USDT-M) станом на: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    futures_data_to_save_txt += "="*40 + "\n\n"
    futures_data_to_save_txt += "--- Ф'ючерсний гаманець (USDT-M) ---\n"
    if futures_usdt_info:
         # Форматуємо дані ф'ючерсів для TXT вручну, оскільки немає таблиці
         futures_data_to_save_txt += f"Актив: {futures_usdt_info['Актив']}\n"
         futures_data_to_save_txt += f"  Баланс гаманця: {futures_usdt_info['Баланс гаманця']:.8f}\n"
         futures_data_to_save_txt += f"  Нереалізований PNL: {futures_usdt_info['Нереалізований PNL']:.8f}\n"
         futures_data_to_save_txt += f"  Загальний баланс активу (в USDT): {futures_usdt_info['Загалом (USDT)']:.8f}\n"
    else:
         futures_data_to_save_txt += "Інформація про актив USDT на ф'ючерсному гаманці USDT-M не знайдена.\n"

    futures_data_to_save_txt += f"\nЗагальний ф'ючерсний баланс (оцінка в USD): {futures_balance_usd:.2f} USD\n"
    futures_data_to_save_txt += "="*40 + "\n"


    # 5. Збереження даних у файли (використовуємо функції з balance.data_processing, передаємо шлях та імена файлів)
    json_output_file_name = 'futures_account_binance_output.json' # Нове ім'я для ф'ючерсів JSON
    txt_output_file_name = 'futures_account_binance_output.txt' # Нове ім'я для ф'ючерсів TXT

    save_to_json(futures_data_to_save_json, output_dir_path=OUTPUT_DIR, file_name=json_output_file_name)
    save_to_txt(futures_data_to_save_txt, output_dir_path=OUTPUT_DIR, file_name=txt_output_file_name)


    logging.info("\nВиконання скрипта futures_account_binance.py завершено.")

# Точка входу при прямому запуску файлу
if __name__ == "__main__":
    main()