import os
import logging
import json
import pandas as pd
# from datetime import datetime # Імпорт datetime тут не потрібен

# Припустимо, логування вже налаштовано в головному скрипті (main.py)
# Функції тут просто використовують існуючий логер

# Функція format_spot_balance_table залишається без змін
def format_spot_balance_table(spot_balances_list):
    """Форматує список спотових балансів у рядок таблиці."""
    if not spot_balances_list:
        return "На спотовому гаманці немає активів з балансом > 0."

    df_spot = pd.DataFrame(spot_balances_list)

    # Форматуємо числові стовбці для вигляду в таблиці
    df_spot['Вільний'] = df_spot['Вільний'].map('{:.8f}'.format)
    df_spot['Заблокований'] = df_spot['Заблокований'].map('{:.8f}'.format)
    df_spot['Всього'] = df_spot['Всього'].map('{:.8f}'.format)
    
    # Обробка стовпця "Вартість (USD)" для виводу (N/A або число)
    df_spot['Вартість (USD)'] = df_spot['Вартість (USD)'].apply(lambda x: f'{x:.2f}' if pd.notna(x) else 'N/A')

    return df_spot.to_string(index=False)


# !!! ОНОВЛЕНО: Функція save_to_json приймає аргумент file_name
def save_to_json(data, output_dir_path, file_name):
    """Зберігає дані у файл JSON з вказаним іменем у вказаній вихідній директорії."""
    output_file_path = os.path.join(output_dir_path, file_name)
    try:
        # Перевіряємо та створюємо папку output, якщо її немає
        if not os.path.exists(output_dir_path):
             os.makedirs(output_dir_path)
             
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Дані збережено у файл JSON: {output_file_path}") # Змінено повідомлення
        return True
    except Exception as e:
        logging.error(f"Помилка при збереженні у файл JSON: {e}")
        return False

# !!! ОНОВЛЕНО: Функція save_to_txt приймає аргумент file_name
def save_to_txt(data_string, output_dir_path, file_name):
    """Зберігає рядок даних у файл TXT з вказаним іменем у вказаній вихідній директорії."""
    output_file_path = os.path.join(output_dir_path, file_name)
    try:
        # Перевіряємо та створюємо папку output, якщо її немає
        if not os.path.exists(output_dir_path):
             os.makedirs(output_dir_path)
             
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(data_string)
        logging.info(f"Дані збережено у файл TXT: {output_file_path}") # Змінено повідомлення
        return True
    except Exception as e:
        logging.error(f"Помилка при збереженні у файл TXT: {e}")
        return False