import os
import logging
from datetime import datetime
import json

# Імпортуємо необхідні функції з нашого пакета 'balance'
# save_to_json, save_to_txt вже імпортовані
from balance.api import load_api_keys, initialize_binance_client, get_spot_balance
from balance.data_processing import format_spot_balance_table, save_to_json, save_to_txt

# --- Визначення шляхів відносно директорії цього скрипта (spot_account_binance.py) ---
# ... (цей блок залишається без змін) ...
SCRIPT_DIR = os.path.dirname(__file__)
SERVICE_DIR = os.path.join(SCRIPT_DIR, 'service')
DOTENV_PATH = os.path.join(SERVICE_DIR, '.env')
LOG_DIR = os.path.join(SCRIPT_DIR, 'balance', 'logs')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'balance', 'output')


# --- Налаштування логування (робимо це тут, в точці входу) ---
# ... (цей блок залишається без змін) ...
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '_spot.log'
log_file_path = os.path.join(LOG_DIR, log_file_name)

if not logging.root.handlers:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(log_file_path, encoding='utf-8'),
                            logging.StreamHandler()
                        ])

# --- Головна логіка виконання цього скрипта ---
def main():
    logging.info("Розпочато виконання скрипта spot_account_binance.py")

    # ... (код отримання балансу залишається без змін) ...
    api_key, secret_key = load_api_keys(dotenv_file_path=DOTENV_PATH)
    if not api_key or not secret_key:
        return
    binance_client = initialize_binance_client(api_key, secret_key)
    if not binance_client:
        return

    logging.info("\nОтримання спотового балансу...")
    spot_list, total_spot_usd = get_spot_balance(binance_client)
    logging.info(f"\nЗагальний спотовий баланс (оцінка в USD): {total_spot_usd:.2f} USD")
    spot_table_string = format_spot_balance_table(spot_list)
    logging.info("\nДеталі спотового балансу:")
    logging.info('\n' + spot_table_string)


    # 5. Підготовка даних для збереження (тільки спотовий баланс)
    current_time = datetime.now()
    spot_data_to_save_json = {
        'timestamp': current_time.isoformat(),
        'spot_balance': {
            'total_estimated_usd': total_spot_usd,
            'assets': spot_list
        }
    }

    spot_data_to_save_txt = f"Звіт про спотовий баланс Binance станом на: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    spot_data_to_save_txt += "="*40 + "\n\n"
    spot_data_to_save_txt += "--- Спотовий гаманець ---\n"
    spot_data_to_save_txt += spot_table_string + "\n"
    spot_data_to_save_txt += f"\nЗагальний спотовий баланс (оцінка в USD): {total_spot_usd:.2f} USD\n"
    spot_data_to_save_txt += "="*40 + "\n"


    # 6. Збереження даних у файли (використовуємо функції з balance.data_processing)
    # !!! ОНОВЛЕНО: Передаємо бажані імена файлів
    json_output_file_name = 'spot_account_binance_output.json'
    txt_output_file_name = 'spot_account_binance_output.txt'

    save_to_json(spot_data_to_save_json, output_dir_path=OUTPUT_DIR, file_name=json_output_file_name)
    save_to_txt(spot_data_to_save_txt, output_dir_path=OUTPUT_DIR, file_name=txt_output_file_name)


    logging.info("\nВиконання скрипта spot_account_binance.py завершено.")

# Точка входу при прямому запуску файлу
if __name__ == "__main__":
    main()