# pro1/balance/report_generator.py
import logging 
from datetime import datetime
from . import data_processing

# ... (prepare_spot_report_data, prepare_futures_report_data, prepare_earn_report_data - без змін) ...
def prepare_spot_report_data(spot_list, total_spot_usd, total_dust_usd=0.0):
    current_time = datetime.now()
    report_name_suffix = "spot_account_binance_output"
    json_data = {
        'timestamp': current_time.isoformat(),
        'spot_balance': {
            'total_estimated_usd': total_spot_usd, 
            'assets': spot_list,
            'total_dust_estimated_usd': total_dust_usd 
        }
    }
    spot_table_string = data_processing.format_spot_balance_table(spot_list)
    txt_data = f"Звіт про спотовий баланс Binance станом на: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    txt_data += "="*40 + "\n\n"
    txt_data += "--- Спотовий гаманець ---\n"
    txt_data += spot_table_string + "\n"
    txt_data += f"\nЗагальний спотовий баланс (без урахування пилу): {total_spot_usd:.2f} USD\n"
    if total_dust_usd > 0:
        txt_data += f"Загальна вартість відфільтрованого 'пилу' на споті: {total_dust_usd:.2f} USD\n"
    txt_data += "="*40 + "\n"
    return json_data, txt_data, report_name_suffix

def prepare_futures_report_data(futures_usdt_info, total_futures_usd): # Це для USDT-M
    current_time = datetime.now()
    report_name_suffix = "futures_usdt_account_binance_output" # Змінено ім'я для уникнення конфлікту
    json_data = {
        'timestamp': current_time.isoformat(),
        'futures_balance_usdt_m': futures_usdt_info
    }
    txt_data = f"Звіт про ф'ючерсний баланс Binance (USDT-M) станом на: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    txt_data += "="*40 + "\n\n"
    txt_data += "--- Ф'ючерсний гаманець (USDT-M) ---\n"
    if futures_usdt_info:
         txt_data += f"Актив: {futures_usdt_info['Актив']}\n"
         txt_data += f"  Баланс гаманця: {futures_usdt_info['Баланс гаманця']:.8f}\n"
         txt_data += f"  Нереалізований PNL: {futures_usdt_info['Нереалізований PNL']:.8f}\n"
         txt_data += f"  Загальний баланс активу (в USDT): {futures_usdt_info['Загалом (USDT)']:.8f}\n"
    else:
         txt_data += "Інформація про актив USDT на ф'ючерсному гаманці USDT-M не знайдена.\n"
    txt_data += f"\nЗагальний USDT-M ф'ючерсний баланс (оцінка в USD): {total_futures_usd:.2f} USD\n"
    txt_data += "="*40 + "\n"
    return json_data, txt_data, report_name_suffix

def prepare_earn_report_data(earn_list, total_earn_usd, total_dust_usd=0.0):
    current_time = datetime.now()
    report_name_suffix = "earn_account_binance_output"
    json_data = {
        'timestamp': current_time.isoformat(),
        'earn_balance': {
             'total_estimated_usd': total_earn_usd, 
             'assets': earn_list,
             'total_dust_estimated_usd': total_dust_usd 
        }
    }
    earn_table_string = data_processing.format_earn_balance_table(earn_list)
    txt_data = f"Звіт про Binance Earn баланс станом на: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    txt_data += "="*40 + "\n\n"
    txt_data += "--- Binance Earn рахунок ---\n"
    txt_data += earn_table_string + "\n" 
    txt_data += f"\nЗагальний Binance Earn баланс (без урахування пилу): {total_earn_usd:.2f} USD\n"
    if total_dust_usd > 0:
        txt_data += f"Загальна вартість відфільтрованого 'пилу' на Earn: {total_dust_usd:.2f} USD\n"
    txt_data += "="*40 + "\n"
    return json_data, txt_data, report_name_suffix

def prepare_coin_m_futures_report_data(coin_m_list, total_coin_m_usd):
    """Готує дані для звіту по COIN-M ф'ючерсному балансу (JSON та TXT)."""
    current_time = datetime.now()
    report_name_suffix = "futures_coin_m_account_binance_output"

    json_data = {
        'timestamp': current_time.isoformat(),
        'futures_balance_coin_m': {
            'total_estimated_usd': total_coin_m_usd,
            'assets': coin_m_list
        }
    }

    coin_m_table_string = data_processing.format_coin_m_futures_balance_table(coin_m_list)

    txt_data = f"Звіт про ф'ючерсний баланс Binance (COIN-M) станом на: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    txt_data += "="*40 + "\n\n"
    txt_data += "--- Ф'ючерсний гаманець (COIN-M) ---\n"
    txt_data += coin_m_table_string + "\n" 
    txt_data += f"\nЗагальний COIN-M ф'ючерсний баланс (оцінка в USD): {total_coin_m_usd:.2f} USD\n"
    txt_data += "="*40 + "\n"
    
    return json_data, txt_data, report_name_suffix


def prepare_full_report_data(
    spot_list, total_spot_usd, total_spot_dust_usd,
    earn_list, total_earn_usd, total_earn_dust_usd,
    usdt_m_futures_info, total_usdt_m_futures_usd, # Змінено для ясності
    coin_m_futures_list, total_coin_m_futures_usd # Додано COIN-M
):
    """Готує дані для повного звіту (JSON та TXT), включаючи всі типи балансів."""
    current_time = datetime.now()
    report_name_suffix = "balance_output" 

    total_estimated_balance_usd = (
        total_spot_usd + 
        total_earn_usd + 
        total_usdt_m_futures_usd +
        total_coin_m_futures_usd
    )
    total_overall_dust_usd = total_spot_dust_usd + total_earn_dust_usd

    json_data = {
        'timestamp': current_time.isoformat(),
        'spot_balance': {
            'total_estimated_usd': total_spot_usd,
            'assets': spot_list,
            'total_dust_estimated_usd': total_spot_dust_usd
        },
        'earn_balance': {
             'total_estimated_usd': total_earn_usd,
             'assets': earn_list,
             'total_dust_estimated_usd': total_earn_dust_usd
        },
        'futures_balance_usdt_m': usdt_m_futures_info, # Зберігаємо інформацію про USDT як єдиний актив
        'futures_balance_coin_m': { # Нова секція для COIN-M
            'total_estimated_usd': total_coin_m_futures_usd,
            'assets': coin_m_futures_list
        },
        'total_balance_estimated_usd': total_estimated_balance_usd,
        'total_dust_across_accounts_usd': total_overall_dust_usd 
    }

    spot_table_string = data_processing.format_spot_balance_table(spot_list)
    earn_table_string = data_processing.format_earn_balance_table(earn_list) 
    coin_m_table_string = data_processing.format_coin_m_futures_balance_table(coin_m_futures_list)


    txt_data = f"Звіт про баланс Binance станом на: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    txt_data += "="*80 + "\n\n" # Збільшимо ширину

    # Spot
    txt_data += "--- Спотовий гаманець ---\n"
    txt_data += spot_table_string + "\n"
    txt_data += f"\nЗагальний спотовий баланс (без урахування пилу): {total_spot_usd:.2f} USD\n"
    if total_spot_dust_usd > 0:
        txt_data += f"Загальна вартість відфільтрованого 'пилу' на споті: {total_spot_dust_usd:.2f} USD\n"
    txt_data += "\n\n"

    # Earn
    txt_data += "--- Binance Earn рахунок ---\n"
    txt_data += earn_table_string + "\n" 
    txt_data += f"\nЗагальний Binance Earn баланс (без урахування пилу): {total_earn_usd:.2f} USD\n"
    if total_earn_dust_usd > 0:
        txt_data += f"Загальна вартість відфільтрованого 'пилу' на Earn: {total_earn_dust_usd:.2f} USD\n"
    txt_data += "\n\n"
    
    # USDT-M Futures
    txt_data += "--- Ф'ючерсний гаманець (USDT-M) ---\n"
    if usdt_m_futures_info:
        txt_data += f"Актив: {usdt_m_futures_info['Актив']}\n"
        txt_data += f"  Баланс гаманця: {usdt_m_futures_info['Баланс гаманця']:.8f}\n"
        txt_data += f"  Нереалізований PNL: {usdt_m_futures_info['Нереалізований PNL']:.8f}\n"
        txt_data += f"  Загальний баланс активу (в USDT): {usdt_m_futures_info['Загалом (USDT)']:.8f}\n"
    else:
        txt_data += "Інформація про актив USDT на ф'ючерсному гаманці USDT-M не знайдена.\n"
    txt_data += f"\nЗагальний USDT-M ф'ючерсний баланс (оцінка в USD): {total_usdt_m_futures_usd:.2f} USD\n\n"

    # COIN-M Futures
    txt_data += "--- Ф'ючерсний гаманець (COIN-M) ---\n"
    txt_data += coin_m_table_string + "\n"
    txt_data += f"\nЗагальний COIN-M ф'ючерсний баланс (оцінка в USD): {total_coin_m_futures_usd:.2f} USD\n\n"


    txt_data += "="*80 + "\n"
    txt_data += f"ЗАГАЛЬНИЙ БАЛАНС (Спот + Earn + USDT-M + COIN-M, без урахування пилу): {total_estimated_balance_usd:.2f} USD\n"
    if total_overall_dust_usd > 0:
        txt_data += f"Загальна вартість відфільтрованого 'пилу' (спот + Earn): {total_overall_dust_usd:.2f} USD\n"
    txt_data += "="*80 + "\n"

    return json_data, txt_data, report_name_suffix