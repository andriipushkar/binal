# pro1/balance/script_runner.py
import logging
from . import config 
from . import api
from . import data_processing
from . import report_generator

def run_balance_script(report_type, calling_script_name="скрипта", dust_threshold=0.01):
    logging.info(f"Функція run_balance_script викликана для звіту типу '{report_type}' зі скрипта '{calling_script_name}'")
    if report_type in ["spot", "earn", "full", "coin_m_futures"]: # Додано coin_m_futures
        logging.info(f"Поріг фільтрації 'пилу' для цього запуску: {dust_threshold:.2f} USD (застосовується до Spot та Earn)")

    api_key, secret_key = api.load_api_keys(dotenv_file_path=config.DOTENV_PATH)
    if not api_key or not secret_key:
        logging.error("Зупинка виконання run_balance_script через відсутність API ключів.")
        return
    
    binance_client = api.initialize_binance_client(api_key, secret_key)
    if not binance_client:
        logging.error("Зупинка виконання run_balance_script через помилку ініціалізації клієнта Binance.")
        return

    json_data_to_save = None
    txt_data_to_save = None
    report_file_suffix_from_generator = "" 
    
    spot_list_data, total_spot_usd_data, total_dust_usd_spot = [], 0.0, 0.0
    earn_list_data, total_earn_usd_data, total_dust_usd_earn = [], 0.0, 0.0
    usdt_m_futures_info_data, total_usdt_m_futures_usd_data = None, 0.0 # Змінено назву
    coin_m_futures_list_data, total_coin_m_futures_usd_data = [], 0.0 # Нові змінні


    if report_type == "spot" or report_type == "full":
        logging.info("\nОтримання спотового балансу...")
        spot_list_data, total_spot_usd_data, total_dust_usd_spot = api.get_spot_balance(binance_client, dust_threshold)
        logging.info(f"\nЗагальний спотовий баланс (без урахування пилу > {dust_threshold:.2f} USD): {total_spot_usd_data:.2f} USD")
        if total_dust_usd_spot > 0:
            logging.info(f"Загальна вартість відфільтрованого 'пилу' на споті: {total_dust_usd_spot:.2f} USD")
        
        if report_type == "spot":
            spot_table_string = data_processing.format_spot_balance_table(spot_list_data)
            logging.info("\nДеталі спотового балансу:")
            logging.info('\n' + spot_table_string)
            json_data_to_save, txt_data_to_save, report_file_suffix_from_generator = \
                report_generator.prepare_spot_report_data(spot_list_data, total_spot_usd_data, total_dust_usd_spot)

    if report_type == "earn" or report_type == "full":
        logging.info("\nОтримання Earn балансу...")
        earn_list_data, total_earn_usd_data, total_dust_usd_earn = api.get_earn_balance(binance_client, dust_threshold)
        logging.info(f"\nЗагальний Binance Earn баланс (без урахування пилу > {dust_threshold:.2f} USD): {total_earn_usd_data:.2f} USD")
        if total_dust_usd_earn > 0:
            logging.info(f"Загальна вартість відфільтрованого 'пилу' на Earn: {total_dust_usd_earn:.2f} USD")
        if report_type == "earn":
            json_data_to_save, txt_data_to_save, report_file_suffix_from_generator = \
                report_generator.prepare_earn_report_data(earn_list_data, total_earn_usd_data, total_dust_usd_earn)

    if report_type == "futures" or report_type == "full": # "futures" тепер означає USDT-M
        logging.info("\nОтримання USDT-M ф'ючерсного балансу...")
        total_usdt_m_futures_usd_data, usdt_m_futures_info_data = api.get_futures_balance(binance_client) # get_futures_balance для USDT-M
        logging.info(f"\nЗагальний USDT-M ф'ючерсний баланс (оцінка в USD): {total_usdt_m_futures_usd_data:.2f} USD")
        if report_type == "futures": # Якщо запит був тільки на USDT-M
            json_data_to_save, txt_data_to_save, report_file_suffix_from_generator = \
                report_generator.prepare_futures_report_data(usdt_m_futures_info_data, total_usdt_m_futures_usd_data)

    if report_type == "coin_m_futures" or report_type == "full": # Новий тип звіту
        logging.info("\nОтримання COIN-M ф'ючерсного балансу...")
        coin_m_futures_list_data, total_coin_m_futures_usd_data = api.get_coin_m_futures_balance(binance_client)
        logging.info(f"\nЗагальний COIN-M ф'ючерсний баланс (оцінка в USD): {total_coin_m_futures_usd_data:.2f} USD")
        if report_type == "coin_m_futures":
            json_data_to_save, txt_data_to_save, report_file_suffix_from_generator = \
                report_generator.prepare_coin_m_futures_report_data(coin_m_futures_list_data, total_coin_m_futures_usd_data)


    if report_type == "full":
        json_data_to_save, txt_data_to_save, report_file_suffix_from_generator = \
            report_generator.prepare_full_report_data(
                spot_list_data, total_spot_usd_data, total_dust_usd_spot,
                earn_list_data, total_earn_usd_data, total_dust_usd_earn,
                usdt_m_futures_info_data, total_usdt_m_futures_usd_data,
                coin_m_futures_list_data, total_coin_m_futures_usd_data # Передаємо дані COIN-M
            )
    
    if not (json_data_to_save and txt_data_to_save and report_file_suffix_from_generator) and \
       report_type not in ["spot", "futures", "earn", "full", "coin_m_futures"]:
        logging.error(f"Не вдалося згенерувати дані для звіту типу: {report_type}")
        return

    if json_data_to_save and txt_data_to_save and report_file_suffix_from_generator:
        json_output_file_name = f'{report_file_suffix_from_generator}.json'
        txt_output_file_name = f'{report_file_suffix_from_generator}.txt'
        
        data_processing.save_to_json(json_data_to_save, output_dir_path=config.OUTPUT_DIR, file_name=json_output_file_name)
        data_processing.save_to_txt(txt_data_to_save, output_dir_path=config.OUTPUT_DIR, file_name=txt_output_file_name)

    logging.info(f"\nЗавершено обробку звіту типу '{report_type}' для скрипта '{calling_script_name}'.")