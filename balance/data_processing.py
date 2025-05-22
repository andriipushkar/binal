# pro1/balance/data_processing.py
import os
import logging
import json
import pandas as pd
# from datetime import datetime # Імпорт datetime тут не потрібен

# Припустимо, логування вже налаштовано в головному скрипті (main.py)
# Функції тут просто використовують існуючий логер

def format_spot_balance_table(spot_balances_list):
    """Форматує список спотових балансів у рядок таблиці."""
    if not spot_balances_list:
        return "На спотовому гаманці немає активів з балансом > 0."

    df_spot = pd.DataFrame(spot_balances_list)

    # Форматуємо числові стовбці для вигляду в таблиці
    if 'Вільний' in df_spot.columns:
        df_spot['Вільний'] = df_spot['Вільний'].map('{:.8f}'.format)
    if 'Заблокований' in df_spot.columns:
        df_spot['Заблокований'] = df_spot['Заблокований'].map('{:.8f}'.format)
    if 'Всього' in df_spot.columns:
        df_spot['Всього'] = df_spot['Всього'].map('{:.8f}'.format)
    
    # Обробка стовпця "Вартість (USD)" для виводу (N/A або число)
    if 'Вартість (USD)' in df_spot.columns:
        df_spot['Вартість (USD)'] = df_spot['Вартість (USD)'].apply(lambda x: f'{x:.2f}' if pd.notna(x) else 'N/A')

    # Переконуємося, що основні колонки існують для виводу
    columns_to_show = ['Актив', 'Вільний', 'Заблокований', 'Всього', 'Вартість (USD)']
    existing_columns = [col for col in columns_to_show if col in df_spot.columns]
    
    return df_spot[existing_columns].to_string(index=False, na_rep='N/A')


def format_earn_balance_table(earn_list):
    """
    Форматує список активів Earn балансу у вигляді текстової таблиці.
    :param earn_list: Список словників з даними Earn балансу.
                      Кожен словник має містити ключі: 'Актив', 'Продукт', 'Всього', 
                      'Вартість (USD)' (опціонально), 'Дата закінчення' (опціонально для Locked).
    :return: Рядкове представлення таблиці.
    """
    if not earn_list:
        return "На рахунку Binance Earn немає активів з балансом > 0."

    # Створюємо DataFrame
    df_earn = pd.DataFrame(earn_list)

    # Визначаємо, чи є хоча б один Locked продукт з датою закінчення, щоб вирішити, чи показувати колонку
    has_end_date = 'Дата закінчення' in df_earn.columns and df_earn['Дата закінчення'].notna().any()

    # Визначаємо колонки для відображення
    columns_to_display = ['Актив', 'Продукт', 'Всього']
    if has_end_date:
        columns_to_display.append('Дата закінчення')
    columns_to_display.append('Вартість (USD)')
    
    # Переконуємося, що всі потрібні колонки існують, заповнюючи відсутні NaN
    for col in columns_to_display:
        if col not in df_earn.columns:
            df_earn[col] = pd.NA # Або None, або відповідне значення за замовчуванням

    df_display = df_earn[columns_to_display].copy() # Працюємо з копією

    # Форматування числових значень
    if 'Всього' in df_display.columns:
        df_display['Всього'] = df_display['Всього'].apply(lambda x: f"{x:.8f}" if pd.notna(x) else 'N/A')
    if 'Вартість (USD)' in df_display.columns:
        df_display['Вартість (USD)'] = df_display['Вартість (USD)'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else 'N/A')
    
    # Заповнюємо NA для текстових колонок, якщо потрібно
    if 'Дата закінчення' in df_display.columns:
        df_display['Дата закінчення'] = df_display['Дата закінчення'].fillna('') # Пустий рядок для Flexible або якщо дати немає
            
    return df_display.to_string(index=False, na_rep='N/A')

def format_coin_m_futures_balance_table(coin_m_futures_list):
    """
    Форматує список активів COIN-M ф'ючерсного балансу у вигляді текстової таблиці.
    :param coin_m_futures_list: Список словників з даними COIN-M балансу.
                                Очікувані ключі: 'Актив', 'Баланс гаманця', 
                                'Нереалізований PNL', 'Загалом в монеті', 
                                'Ціна (USD)', 'Вартість (USD)'.
    :return: Рядкове представлення таблиці.
    """
    if not coin_m_futures_list:
        return "На COIN-M ф'ючерсному рахунку немає активів для відображення."

    df_coin_m = pd.DataFrame(coin_m_futures_list)

    # Визначаємо колонки для відображення
    columns_to_display = [
        'Актив', 
        'Баланс гаманця', 
        'Нереалізований PNL', 
        'Загалом в монеті', 
        'Ціна (USD)', 
        'Вартість (USD)'
    ]
    
    # Переконуємося, що всі потрібні колонки існують, заповнюючи відсутні pd.NA
    for col in columns_to_display:
        if col not in df_coin_m.columns:
            df_coin_m[col] = pd.NA 

    df_display = df_coin_m[columns_to_display].copy()

    # Форматування числових значень
    numeric_8_decimals = ['Баланс гаманця', 'Нереалізований PNL', 'Загалом в монеті']
    numeric_2_decimals_usd = ['Ціна (USD)', 'Вартість (USD)']

    for col in numeric_8_decimals:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(lambda x: f"{x:.8f}" if pd.notna(x) and isinstance(x, (int, float)) else 'N/A')
    
    for col in numeric_2_decimals_usd:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) and isinstance(x, (int, float)) else 'N/A')
            
    return df_display.to_string(index=False, na_rep='N/A')


def save_to_json(data, output_dir_path, file_name):
    """Зберігає дані у файл JSON з вказаним іменем у вказаній вихідній директорії."""
    output_file_path = os.path.join(output_dir_path, file_name)
    try:
        # Перевіряємо та створюємо папку output, якщо її немає
        if not os.path.exists(output_dir_path):
             os.makedirs(output_dir_path)
             
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Дані збережено у файл JSON: {output_file_path}")
        return True
    except Exception as e:
        logging.error(f"Помилка при збереженні у файл JSON ({output_file_path}): {e}")
        return False

def save_to_txt(data_string, output_dir_path, file_name):
    """Зберігає рядок даних у файл TXT з вказаним іменем у вказаній вихідній директорії."""
    output_file_path = os.path.join(output_dir_path, file_name)
    try:
        # Перевіряємо та створюємо папку output, якщо її немає
        if not os.path.exists(output_dir_path):
             os.makedirs(output_dir_path)
             
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(data_string)
        logging.info(f"Дані збережено у файл TXT: {output_file_path}")
        return True
    except Exception as e:
        logging.error(f"Помилка при збереженні у файл TXT ({output_file_path}): {e}")
        return False