import os
import logging
from datetime import datetime
import json

# Імпортуємо функції з наших модулів всередині пакету balance
# get_earn_balance тепер імпортується тут
from . import api
from . import data_processing
from .api import get_earn_balance # Явне імпортування для використання в main


# --- Визначення шляхів відносно директорії main.py ---
# main.py знаходиться в pro1/balance/
SCRIPT_DIR = os.path.dirname(__file__)
# Папка service знаходиться на один рівень вище (в pro1)
SERVICE_DIR = os.path.join(SCRIPT_DIR, '..', 'service')
DOTENV_PATH = os.path.join(SERVICE_DIR, '.env')

# Папки logs та output знаходяться поруч з main.py (в pro1/balance)
LOG_DIR = os.path.join(SCRIPT_DIR, 'logs')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')


# --- Налаштування логування (робимо це тут, в головному файлі) ---
# Перевіряємо та створюємо папку logs, якщо її немає
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Формат імені файлу логу:YYYY-MM-DD_HH-MM-SS.log
log_file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.log'
log_file_path = os.path.join(LOG_DIR, log_file_name)

# Налаштовуємо базову конфігурацію логування лише один раз
if not logging.root.handlers:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(log_file_path, encoding='utf-8'),
                            logging.StreamHandler() # Вивід у консоль
                        ])


# --- Головна функція виконання ---
def main():
    logging.info("Розпочато виконання головного скрипта.")

    # 1. Завантаження API ключів (передаємо шлях до .env)
    dotenv_path_from_main = os.path.join(os.path.dirname(__file__), '..', 'service', '.env')
    api_key, secret_key = api.load_api_keys(dotenv_file_path=dotenv_path_from_main)

    if not api_key or not secret_key:
        # Повідомлення про помилку вже було в load_api_keys
        return # Зупиняємо виконання

    # 2. Ініціалізація клієнта Binance API
    binance_client = api.initialize_binance_client(api_key, secret_key)
    if not binance_client:
        # Повідомлення про помилку вже було в initialize_binance_client
        return # Зупиняємо виконання

    logging.info("\nОтримання балансу...")

    # 3. Отримання спотового балансу
    spot_list, total_spot_usd = api.get_spot_balance(binance_client)
    logging.info(f"\nЗагальний спотовий баланс (оцінка в USD): {total_spot_usd:.2f} USD")

    # !!! 4. Отримання Earn балансу !!!
    earn_list, total_earn_usd = api.get_earn_balance(binance_client)
    logging.info(f"\nЗагальний Binance Earn баланс (оцінка в USD): {total_earn_usd:.2f} USD")


    # 5. Отримання ф'ючерсного балансу
    total_futures_usdt, futures_usdt_info = api.get_futures_balance(binance_client)
    futures_balance_usd = total_futures_usdt # Для USDT-M ф'ючерсів оцінка в USD = баланс в USDT
    logging.info(f"\nЗагальний ф'ючерсний баланс (оцінка в USD): {futures_balance_usd:.2f} USD")

    # 6. Форматування даних для виводу у консоль/лог та TXT
    spot_table_string = data_processing.format_spot_balance_table(spot_list)
    logging.info("\nСпотовий баланс:")
    logging.info('\n' + spot_table_string) # Виводимо відформатовану таблицю

    # Для Earn можна теж зробити форматовану таблицю, якщо потрібно
    # earned_table_string = data_processing.format_earn_balance_table(earn_list) # Потрібно створити нову функцію форматування
    # logging.info("\nBinance Earn баланс:")
    # logging.info('\n' + earned_table_string)


    # 7. Підготовка загальних даних для збереження (Включаємо Earn)
    current_time = datetime.now()
    data_for_json = {
        'timestamp': current_time.isoformat(),
        'spot_balance': {
            'total_estimated_usd': total_spot_usd,
            'assets': spot_list
        },
        'earn_balance': { # Нова секція для Earn в JSON
             'total_estimated_usd': total_earn_usd,
             'assets': earn_list # Список активів Earn
        },
        'futures_balance_usdt_m': futures_usdt_info,
        'total_balance_estimated_usd': total_spot_usd + total_earn_usd + futures_balance_usd # Оновлено загальний баланс
    }

    # Підготовка текстового виводу (Включаємо Earn)
    txt_output_content = f"Звіт про баланс Binance станом на: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    txt_output_content += "="*40 + "\n\n"

    txt_output_content += "--- Спотовий гаманець ---\n"
    txt_output_content += spot_table_string + "\n" # Додаємо відформатовану таблицю
    txt_output_content += f"\nЗагальний спотовий баланс (оцінка в USD): {total_spot_usd:.2f} USD\n\n"

    # !!! Нова секція для Earn в TXT !!!
    txt_output_content += "--- Binance Earn рахунок ---\n"
    if earn_list:
         # Якщо не робили окрему функцію форматування, форматуємо тут вручну
         for item in earn_list:
              # item.get('Продукт', 'Earn') - використовуємо .get для безпеки, якщо Продукт відсутній
              txt_output_content += f"  {item['Актив']} ({item.get('Продукт', 'Earn')}): {item['Всього']:.8f}"
              if item.get('Вартість (USD)') is not None:
                  txt_output_content += f" (~{item['Вартість (USD)']:.2f} USD)"
              txt_output_content += "\n"
    else:
         txt_output_content += "На рахунку Binance Earn немає активів з балансом > 0 (або не знайдено підтримуваних продуктів).\n"
    txt_output_content += f"\nЗагальний Binance Earn баланс (оцінка в USD): {total_earn_usd:.2f} USD\n\n"


    txt_output_content += "--- Ф'ючерсний гаманець (USDT-M) ---\n"
    if futures_usdt_info:
        txt_output_content += f"Актив: {futures_usdt_info['Актив']}\n"
        txt_output_content += f"  Баланс гаманця: {futures_usdt_info['Баланс гаманця']:.8f}\n"
        txt_output_content += f"  Нереалізований PNL: {futures_usdt_info['Нереалізований PNL']:.8f}\n"
        txt_output_content += f"  Загальний баланс активу (в USDT): {futures_usdt_info['Загалом (USDT)']:.8f}\n"
    else:
        txt_output_content += "Інформація про актив USDT на ф'ючерсному гаманці USDT-M не знайдена.\n"
    txt_output_content += f"\nЗагальний ф'ючерсний баланс (оцінка в USD): {futures_balance_usd:.2f} USD\n\n"

    txt_output_content += "="*40 + "\n"
    txt_output_content += f"Загальний баланс (спот + Earn + ф'ючерси, оцінка в USD): {total_spot_usd + total_earn_usd + futures_balance_usd:.2f} USD\n" # Оновлено загальний підсумок


    # 8. Збереження даних у файли (передаємо шлях до папки output)
    json_output_file_name = 'balance_output.json'
    txt_output_file_name = 'balance_output.txt'

    data_processing.save_to_json(data_for_json, output_dir_path=OUTPUT_DIR, file_name=json_output_file_name)
    data_processing.save_to_txt(txt_output_content, output_dir_path=OUTPUT_DIR, file_name=txt_output_file_name)


    logging.info("\nВиконання головного скрипта завершено.")

# Точка входу при прямому запуску файлу main.py
if __name__ == "__main__":
    main()