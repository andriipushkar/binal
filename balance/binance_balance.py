import os
import logging
import json
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
from datetime import datetime

# --- Визначення шляхів відносно директорії скрипта ---
# Визначаємо шлях до директорії, де знаходиться цей скрипт
SCRIPT_DIR = os.path.dirname(__file__)
SERVICE_DIR = os.path.join(SCRIPT_DIR, '..', 'service')
DOTENV_PATH = os.path.join(SERVICE_DIR, '.env')
LOG_DIR = os.path.join(SCRIPT_DIR, 'logs')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')

# --- Налаштування логування ---
# Ця конфігурація буде застосована при першому виклику функцій логування
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.log'
log_file_path = os.path.join(LOG_DIR, log_file_name)

# Перевіряємо, чи вже налаштовано логування, щоб уникнути повторного налаштування при імпорті
if not logging.root.handlers:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(log_file_path, encoding='utf-8'),
                            logging.StreamHandler()
                        ])

# --- Функції для роботи з Binance API та даними ---

def load_api_keys(dotenv_file_path):
    """Завантажує API ключі зі змінних оточення або файлу .env."""
    load_dotenv(dotenv_path=dotenv_file_path)
    api_key = os.environ.get('BINANCE_API_KEY')
    secret_key = os.environ.get('BINANCE_SECRET_KEY')
    
    if not api_key or not secret_key:
        logging.error("Помилка: API ключі не завантажено.")
        logging.error(f"Перевірте файл .env за шляхом: {os.path.abspath(dotenv_file_path)}")
        return None, None
        
    logging.info("API ключі завантажено.")
    return api_key, secret_key

def initialize_binance_client(api_key, secret_key):
    """Ініціалізує клієнта Binance API."""
    if not api_key or not secret_key:
        logging.error("Не можу ініціалізувати клієнта: відсутні API ключі.")
        return None
        
    try:
        client = Client(api_key, secret_key)
        # Перевірка підключення
        client.get_server_time()
        logging.info("Успішно підключено до Binance API.")
        return client

    except BinanceAPIException as e:
        logging.error(f"Помилка Binance API при підключенні: {e}")
        if "API-key format invalid" in str(e) or "Signature verification failed" in str(e) or "Permission denied" in str(e):
             logging.error("Перевірте правильність API ключів та дозволів у налаштуваннях Binance.")
        return None
    except Exception as e:
        logging.error(f"Невідома помилка при підключенні: {e}")
        return None

# Функція для отримання ціни активу в USD з кешуванням (з невеликою зміною для прийому client)
price_cache = {} # Кеш цін, оголошений на глобальному рівні модуля

def get_price_in_usd(symbol, client):
    """
    Отримує поточну ціну символу у парі з USDT, BUSD, BTC або BNB (з кешуванням).
    Якщо пряма пара зі стейблкоїном не знайдена, спробує конвертувати через BTC або BNB.
    """
    # Перевірка кешу
    cached_price = price_cache.get(symbol)
    if cached_price is not None:
        return cached_price

    # Обробка стейблкоїнів - їх вартість приблизно 1 USD
    if symbol in ['USDT', 'BUSD', 'USDC', 'DAI', 'UST', 'USD']:
         price_cache[symbol] = 1.0
         return 1.0

    # 1. Спроба знайти пряму пару зі стейблкоїном (USDT, BUSD)
    stablecoin_pairs_to_try = ['USDT', 'BUSD']

    for stablecoin in stablecoin_pairs_to_try:
        stablecoin_symbol = f"{symbol}{stablecoin}"
        try:
            ticker = client.get_symbol_ticker(symbol=stablecoin_symbol)
            price = float(ticker['price'])
            price_cache[symbol] = price # Кешуємо знайдену ціну
            return price
        except BinanceAPIException as e:
            pass
        except Exception as e:
             logging.error(f"Помилка при отриманні ціни для {stablecoin_symbol}: {e}")

    # 2. Якщо пряма пара зі стейблкоїном не знайдена, спробуємо конвертувати через BTC
    btc_pair_symbol = f"{symbol}BTC"
    try:
        btc_ticker = client.get_symbol_ticker(symbol=btc_pair_symbol)
        price_in_btc = float(btc_ticker['price'])

        # Отримуємо ціну BTC в USDT (передаємо client)
        btc_usdt_price = get_price_in_usd('BTC', client) 

        if btc_usdt_price is not None:
            price_in_usd = price_in_btc * btc_usdt_price
            price_cache[symbol] = price_in_usd # Кешуємо розраховану ціну
            return price_in_usd
        else:
            logging.warning(f"Не вдалося отримати ціну BTCUSDT для конвертації {symbol}.")

    except BinanceAPIException as e:
        pass
    except Exception as e:
         logging.error(f"Помилка при конвертації {symbol} через BTC: {e}")

    # 3. Якщо через BTC не вдалося, спробуємо конвертувати через BNB
    bnb_pair_symbol = f"{symbol}BNB"
    try:
        bnb_ticker = client.get_symbol_ticker(symbol=bnb_pair_symbol)
        price_in_bnb = float(bnb_ticker['price'])

        # Отримуємо ціну BNB в USDT (передаємо client)
        bnb_usdt_price = get_price_in_usd('BNB', client) 

        if bnb_usdt_price is not None:
            price_in_usd = price_in_bnb * bnb_usdt_price
            price_cache[symbol] = price_in_usd
            return price_in_usd
        else:
            logging.warning(f"Не вдалося отримати ціну BNBUSDT для конвертації {symbol}.")

    except BinanceAPIException as e:
        pass
    except Exception as e:
         logging.error(f"Помилка при конвертації {symbol} через BNB: {e}")

    # 4. Якщо жоден зі способів не спрацював
    logging.warning(f"Не вдалося отримати ціну для {symbol} у парі зі стейблкоїном, BTC або BNB.")
    price_cache[symbol] = None
    return None

def get_spot_balance(client):
    """Отримує спотовий баланс та розраховує його вартість у USD."""
    spot_balances_list = []
    total_spot_value_usd = 0.0

    logging.info("\n--- Отримання спотового балансу ---")
    try:
        account_info = client.get_account()

        assets_with_balance = False
        for balance in account_info['balances']:
            asset = balance['asset']
            free_balance = float(balance['free'])
            locked_balance = float(balance['locked'])
            total_asset_balance = free_balance + locked_balance

            if total_asset_balance > 0:
                assets_with_balance = True
                
                asset_value_in_usd = 0 # Значення за замовчуванням, якщо ціну не отримано
                price_in_usd = get_price_in_usd(asset, client) # Передаємо client
                
                if price_in_usd is not None:
                     asset_value_in_usd = total_asset_balance * price_in_usd
                     total_spot_value_usd += asset_value_in_usd

                # Додаємо дані активу до списку для JSON та подальшого форматування
                spot_balances_list.append({
                    'Актив': asset,
                    'Вільний': free_balance,
                    'Заблокований': locked_balance,
                    'Всього': total_asset_balance,
                    'Вартість (USD)': asset_value_in_usd if price_in_usd is not None else None
                })

        if not assets_with_balance:
            logging.info("На спотовому гаманці немає активів з балансом > 0.")

        return spot_balances_list, total_spot_value_usd

    except BinanceAPIException as e:
        logging.error(f"Помилка при отриманні спотового балансу: {e}")
        return [], 0.0
    except Exception as e:
        logging.error(f"Невідома помилка при отриманні спотового балансу: {e}")
        return [], 0.0


def get_futures_balance(client):
    """Отримує ф'ючерсний баланс USDT-M."""
    futures_total_usdt = 0.0
    futures_usdt_info = None

    logging.info("\n--- Отримання ф'ючерсного балансу (USDT-M) ---")
    try:
        futures_account_info = client.futures_account()

        usdt_info_found = False
        for asset_info in futures_account_info['assets']:
             if asset_info['asset'] == 'USDT':
                 usdt_info_found = True
                 wallet_balance = float(asset_info['walletBalance'])
                 unrealized_pnl = float(asset_info['unrealizedProfit'])
                 futures_total_usdt = wallet_balance + unrealized_pnl
                 
                 logging.info(f"Актив: {asset_info['asset']}")
                 logging.info(f"  Баланс гаманця: {wallet_balance:.8f}")
                 logging.info(f"  Нереалізований PNL: {unrealized_pnl:.8f}")
                 logging.info(f"  Загальний баланс активу (в USDT): {futures_total_usdt:.8f}")

                 # Зберігаємо дані USDT для JSON
                 futures_usdt_info = {
                     'Актив': asset_info['asset'],
                     'Баланс гаманця': wallet_balance,
                     'Нереалізований PNL': unrealized_pnl,
                     'Загалом (USDT)': futures_total_usdt
                 }

                 break # Знайшли USDT, виходимо з циклу

        if not usdt_info_found:
             logging.info("Інформація про актив USDT на ф'ючерсному гаманці USDT-M не знайдена.")
             logging.info("Можливо, у вас не активований ф'ючерсний акаунт USDT-M або використовується інший тип ф'ючерсів (наприклад, COIN-M).")

        return futures_total_usdt, futures_usdt_info

    except BinanceAPIException as e:
        logging.error(f"Помилка при отриманні ф'ючерсного балансу: {e}")
        if "Margin is not enabled" in str(e) or "You don't have permission" in str(e) or "Invalid API-key, IP, or permissions" in str(e):
             logging.error("Можливо, у вас не активований ф'ючерсний акаунт USDT-M або API ключ не має дозволу на ф'ючерси.")
        return 0.0, None
    except Exception as e:
        logging.error(f"Невідома помилка при отриманні ф'ючерсного балансу: {e}")
        return 0.0, None

def format_spot_balance_table(spot_balances_list):
    """Форматує список спотових балансів у рядок таблиці."""
    if not spot_balances_list:
        return "На спотовому гаманці немає активів з балансом > 0."

    df_spot = pd.DataFrame(spot_balances_list)

    # Форматуємо числові стовпці для вигляду в таблиці
    df_spot['Вільний'] = df_spot['Вільний'].map('{:.8f}'.format)
    df_spot['Заблокований'] = df_spot['Заблокований'].map('{:.8f}'.format)
    df_spot['Всього'] = df_spot['Всього'].map('{:.8f}'.format)
    
    # Обробка стовпця "Вартість (USD)" для виводу (N/A або число)
    df_spot['Вартість (USD)'] = df_spot['Вартість (USD)'].apply(lambda x: f'{x:.2f}' if pd.notna(x) else 'N/A')

    return df_spot.to_string(index=False)


def save_to_json(data, output_file_path):
    """Зберігає дані у файл JSON."""
    try:
        if not os.path.exists(os.path.dirname(output_file_path)):
             os.makedirs(os.path.dirname(output_file_path))
             
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Дані балансу збережено у файл JSON: {output_file_path}")
        return True
    except Exception as e:
        logging.error(f"Помилка при збереженні у файл JSON: {e}")
        return False

def save_to_txt(data, output_file_path):
    """Зберігає дані у файл TXT."""
    try:
        if not os.path.exists(os.path.dirname(output_file_path)):
             os.makedirs(os.path.dirname(output_file_path))
             
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(data)
        logging.info(f"Дані балансу збережено у файл TXT: {output_file_path}")
        return True
    except Exception as e:
        logging.error(f"Помилка при збереженні у файл TXT: {e}")
        return False

# --- Головна логіка виконання скрипта ---
# Цей блок виконається лише при прямому запуску файлу, а не при імпорті як модуля
if __name__ == "__main__":
    logging.info("Виконання як основного скрипта.")

    # 1. Завантаження API ключів
    api_key, secret_key = load_api_keys(DOTENV_PATH)
    if not api_key or not secret_key:
        exit() # Зупиняємо виконання, якщо ключі не завантажено

    # 2. Ініціалізація клієнта Binance API
    binance_client = initialize_binance_client(api_key, secret_key)
    if not binance_client:
        exit() # Зупиняємо виконання, якщо клієнт не ініціалізовано

    logging.info("\nОтримання балансу...")

    # 3. Отримання спотового балансу
    spot_list, total_spot_usd = get_spot_balance(binance_client)
    logging.info(f"\nЗагальний спотовий баланс (оцінка в USD): {total_spot_usd:.2f} USD")

    # 4. Отримання ф'ючерсного балансу
    total_futures_usdt, futures_usdt_info = get_futures_balance(binance_client)
    futures_balance_usd = total_futures_usdt # Для USDT-M ф'ючерсів оцінка в USD = баланс в USDT
    logging.info(f"\nЗагальний ф'ючерсний баланс (оцінка в USD): {futures_balance_usd:.2f} USD")

    # 5. Форматування даних для виводу у консоль/лог та TXT
    spot_table_string = format_spot_balance_table(spot_list)
    logging.info("\nСпотовий баланс:")
    logging.info('\n' + spot_table_string) # Виводимо відформатовану таблицю


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
    txt_output_content += spot_table_string + "\n" # Додаємо відформатовану таблицю
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
    json_output_path = os.path.join(OUTPUT_DIR, 'balance_output.json')
    txt_output_path = os.path.join(OUTPUT_DIR, 'balance_output.txt')

    save_to_json(data_for_json, json_output_path)
    save_to_txt(txt_output_content, txt_output_path)


    logging.info("\nВиконання основного скрипта завершено.")