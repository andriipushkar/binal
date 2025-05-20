import os
import logging
from datetime import datetime
import json

# Імпортуємо необхідні функції з нашого пакета 'balance'
from balance import api
from balance import data_processing

# --- Визначення шляхів відносно директорії цього скрипта (balance_binance.py) ---
# balance_binance.py знаходиться в pro1/
SCRIPT_DIR = os.path.dirname(__file__)
# Папка service знаходиться поруч з цим скриптом
SERVICE_DIR = os.path.join(SCRIPT_DIR, 'service')
DOTENV_PATH = os.path.join(SERVICE_DIR, '.env')

# Папки logs та output знаходяться всередині папки balance/
LOG_DIR = os.path.join(SCRIPT_DIR, 'balance', 'logs')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'balance', 'output')


# --- Налаштування логування (робимо це тут, в точці входу) ---
# Перевіряємо та створюємо папку logs, якщо її немає
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Формат імені файлу логу:<\ctrl97>code]YYYY-MM-DD_HH-MM-SS.log[/%code]
log_file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.log' # Лог для balance_binance.py без _spot
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
    logging.info("Розпочато виконання скрипта balance_binance.py")

    # ... (код отримання балансу залишається без змін) ...
    api_key, secret_key = api.load_api_keys(dotenv_file_path=DOTENV_PATH)
    if not api_key or not secret_key:
        return
    binance_client = api.initialize_binance_client(api_key, secret_key)
    if not binance_client:
        return

    logging.info("\nОтримання балансу...")

    spot_list, total_spot_usd = api.get_spot_balance(binance_client)
    logging.info(f"\nЗагальний спотовий баланс (оцінка в USD): {total_spot_usd:.2f} USD")

    total_futures_usdt, futures_usdt_info = api.get_futures_balance(binance_client)
    futures_balance_usd = total_futures_usdt
    logging.info(f"\nЗагальний ф'ючерсний баланс (оцінка в USD): {futures_balance_usd:.2f} USD")

    spot_table_string = data_processing.format_spot_balance_table(spot_list)
    logging.info("\nСпотовий баланс:")
    logging.info('\n' + spot_table_string)


    # 6. Підготовка загальних даних для збереження
    current_time = datetime.now()
    data_for_json = {
        'timestamp': current_time.isoformat(),
        'spot_balance': {
            'total_estimated_usd': total_spot_usd,
            'assets': spot_list
        },
        'futures_balance_usdt_m': futures_usdt_info,
        'total_balance_estimated_usd': total_spot_usd + futures_balance_usd
    }

    txt_output_content = f"Звіт про баланс Binance станом на: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    txt_output_content += "="*40 + "\n\n"
    txt_output_content += "--- Спотовий гаманець ---\n"
    txt_output_content += spot_table_string + "\n"
    txt_output_content += f"\nЗагальний спотовий баланс (оцінка в USD): {total_spot_usd:.2f} USD\n\n"
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
    txt_output_content += f"Загальний баланс (спот + ф'ючерси, оцінка в USD): {total_spot_usd + futures_balance_usd:.2f} USD\n"


    # 7. Збереження даних у файли
    # !!! ОНОВЛЕНО: Передаємо бажані імена файлів для balance_binance.py
    json_output_file_name = 'balance_output.json' # Використовуємо оригінальне ім'я
    txt_output_file_name = 'balance_output.txt' # Використовуємо оригінальне ім'я

    data_processing.save_to_json(data_for_json, output_dir_path=OUTPUT_DIR, file_name=json_output_file_name)
    data_processing.save_to_txt(txt_output_content, output_dir_path=OUTPUT_DIR, file_name=txt_output_file_name)


    logging.info("\nВиконання скрипта balance_binance.py завершено.")

# Точка входу при прямому запуску файлу
if __name__ == "__main__":
    main()