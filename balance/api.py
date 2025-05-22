# pro1/balance/api.py
import os
import logging
import time 
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException 
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects 

# Припустимо, логування вже налаштовано в головному скрипті (main.py або зовнішньому)

price_cache = {}

# --- Декоратор для повторних спроб ---
def retry_on_exception(retries=3, delay=5, allowed_exceptions_tuple=None):
    """
    Декоратор для повторного виконання функції у разі виникнення певних винятків.
    :param retries: Максимальна кількість спроб.
    :param delay: Затримка між спробами в секундах.
    :param allowed_exceptions_tuple: Кортеж винятків, при яких слід повторювати спробу.
    """
    # Встановлюємо стандартні винятки, якщо користувач не передав свої
    if allowed_exceptions_tuple is None:
        effective_allowed_exceptions = (
            BinanceRequestException, # Загальна помилка запиту Binance (може бути тимчасовою)
            ConnectionError,
            Timeout,
            TooManyRedirects
        )
    else:
        effective_allowed_exceptions = allowed_exceptions_tuple

    def decorator(func):
        def wrapper(*args, **kwargs):
            current_retries = retries
            while current_retries > 0:
                try:
                    return func(*args, **kwargs)
                except BinanceAPIException as e_api:
                    # НЕ робимо retry для "Invalid symbol"
                    if e_api.code == -1121 and "Invalid symbol" in str(e_api):
                        # logging.debug(f"Функція {func.__name__} викликала 'Invalid symbol': {e_api}. Не повторюємо.")
                        raise  # Прокидаємо "Invalid symbol" далі
                    
                    # Для інших BinanceAPIException робимо retry
                    current_retries -= 1
                    logging.warning(
                        f"Функція {func.__name__} викликала помилку Binance API: {e_api}. "
                        f"Залишилося спроб: {current_retries}. Повторна спроба через {delay} сек."
                    )
                    if current_retries == 0:
                        logging.error(
                            f"Функція {func.__name__} не виконалася успішно (Binance API Error: {e_api}) після {retries} спроб."
                        )
                        raise
                    time.sleep(delay)

                except effective_allowed_exceptions as e_net: # Обробляємо інші дозволені мережеві винятки
                    current_retries -= 1
                    logging.warning(
                        f"Функція {func.__name__} викликала мережеву помилку: {e_net}. "
                        f"Залишилося спроб: {current_retries}. Повторна спроба через {delay} сек."
                    )
                    if current_retries == 0:
                        logging.error(
                            f"Функція {func.__name__} не виконалася успішно (Мережева помилка: {e_net}) після {retries} спроб."
                        )
                        raise
                    time.sleep(delay)
            # Цей return ніколи не має спрацювати, якщо цикл while завершився без успішного func()
            # або без прокидання винятку після вичерпання спроб.
            return None 
        return wrapper
    return decorator

# --- Функції API ---

def load_api_keys(dotenv_file_path):
    """Завантажує API ключі зі змінних оточення або файлу .env за вказаним шляхом."""
    if not os.path.exists(dotenv_file_path):
        logging.error(f"Помилка: Файл .env не знайдено за шляхом: {os.path.abspath(dotenv_file_path)}")
        return None, None

    load_dotenv(dotenv_path=dotenv_file_path)
    api_key = os.environ.get('BINANCE_API_KEY')
    secret_key = os.environ.get('BINANCE_SECRET_KEY')

    if not api_key or not secret_key:
        logging.error("Помилка: API ключі не завантажено з .env файлу.")
        logging.error("Перевірте, чи встановлено змінні 'BINANCE_API_KEY' та 'BINANCE_SECRET_KEY' у файлі.")
        return None, None

    logging.info("API ключі завантажено.")
    return api_key, secret_key

@retry_on_exception(retries=3, delay=5, allowed_exceptions_tuple=(BinanceAPIException, BinanceRequestException, ConnectionError, Timeout, TooManyRedirects))
def _get_server_time_with_retry(client_instance):
    """Допоміжна функція для виклику client.get_server_time() з retry."""
    return client_instance.get_server_time()

def initialize_binance_client(api_key, secret_key):
    """Ініціалізує клієнта Binance API."""
    if not api_key or not secret_key:
        logging.error("Не можу ініціалізувати клієнта: відсутні API ключі.")
        return None
    try:
        client = Client(api_key, secret_key)
        _get_server_time_with_retry(client) # Перевірка підключення з retry
        logging.info("Успішно підключено до Binance API.")
        return client
    except Exception as e:
        logging.error(f"Не вдалося підключитися до Binance API після кількох спроб: {e}")
        if isinstance(e, BinanceAPIException) and \
           ("API-key format invalid" in str(e) or \
            "Signature verification failed" in str(e) or \
            "Permission denied" in str(e)):
             logging.error("Перевірте правильність API ключів та дозволів у налаштуваннях Binance.")
        return None

@retry_on_exception(retries=3, delay=2, allowed_exceptions_tuple=(BinanceAPIException, BinanceRequestException, ConnectionError, Timeout, TooManyRedirects))
def get_ticker_price_raw(client, symbol_pair):
    """
    Базова функція для отримання ціни, до якої застосовується retry.
    "Invalid symbol" буде прокинута декоратором і має бути оброблена у get_price_in_usd.
    """
    ticker = client.get_symbol_ticker(symbol=symbol_pair)
    return float(ticker['price'])

def _try_get_price_via_stablecoin(symbol, client, stablecoin):
    stablecoin_symbol = f"{symbol}{stablecoin}"
    try:
        price = get_ticker_price_raw(client, stablecoin_symbol)
        logging.debug(f"Ціну для {symbol} знайдено через пару {stablecoin_symbol}: {price}")
        return price
    except BinanceAPIException as e: 
        if e.code == -1121 and "Invalid symbol" in str(e):
            logging.debug(f"Пари {stablecoin_symbol} не існує.")
            return None 
        else:
            logging.warning(f"Не вдалося отримати ціну для {stablecoin_symbol} після спроб (інша помилка API): {e}")
            return None 
    except Exception as e: 
        logging.error(f"Неочікувана помилка при отриманні ціни для {stablecoin_symbol}: {e}")
        return None

def _try_get_price_via_conversion(symbol, client, conversion_asset): 
    pair_symbol = f"{symbol}{conversion_asset}"
    try:
        price_in_conversion_asset = get_ticker_price_raw(client, pair_symbol)
        conversion_asset_usd_price = get_price_in_usd(conversion_asset, client) 
        if conversion_asset_usd_price is not None:
            price_in_usd = price_in_conversion_asset * conversion_asset_usd_price
            logging.debug(f"Ціну для {symbol} розраховано через {conversion_asset} ({pair_symbol}): {price_in_usd}")
            return price_in_usd
        else:
            logging.warning(f"Не вдалося отримати ціну {conversion_asset}USDT для конвертації {symbol}.")
            return None
    except BinanceAPIException as e: 
        if e.code == -1121 and "Invalid symbol" in str(e):
            logging.debug(f"Пари {pair_symbol} не існує.")
            return None
        else:
            logging.warning(f"Не вдалося конвертувати {symbol} через {conversion_asset} після спроб (інша помилка API): {e}")
            return None
    except Exception as e:
         logging.error(f"Неочікувана помилка при конвертації {symbol} через {conversion_asset}: {e}")
         return None

def get_price_in_usd(symbol, client):
    """
    Отримує поточну оціночну ціну символу в USD.
    Використовує кешування та різні стратегії: прямі пари зі стейблкоїнами, конвертація через BTC/BNB.
    """
    cached_price = price_cache.get(symbol)
    if cached_price is not None:
        return cached_price

    if symbol in ['USDT', 'BUSD', 'USDC', 'DAI', 'UST', 'USD']: 
         price_cache[symbol] = 1.0
         return 1.0

    stablecoins_to_try = ['USDT', 'BUSD']
    for stablecoin in stablecoins_to_try:
        price = _try_get_price_via_stablecoin(symbol, client, stablecoin)
        if price is not None:
            price_cache[symbol] = price
            return price

    price = _try_get_price_via_conversion(symbol, client, 'BTC')
    if price is not None:
        price_cache[symbol] = price
        return price

    price = _try_get_price_via_conversion(symbol, client, 'BNB')
    if price is not None:
        price_cache[symbol] = price
        return price
    
    logging.warning(f"Не вдалося отримати ціну для {symbol} жодним зі способів.")
    price_cache[symbol] = None 
    return None

@retry_on_exception(allowed_exceptions_tuple=(BinanceAPIException, BinanceRequestException, ConnectionError, Timeout, TooManyRedirects))
def get_account_details_with_retry(client):
    return client.get_account()

def get_spot_balance(client, dust_threshold=0.01):
    """
    Отримує спотовий баланс, фільтруючи "пил" та розраховує його вартість у USD.
    Повертає список відфільтрованих активів, їх загальну вартість та загальну вартість "пилу".
    """
    spot_balances_list = []
    total_spot_value_usd = 0.0
    total_dust_value_usd = 0.0 

    logging.info(f"--- Отримання спотового балансу (поріг пилу: {dust_threshold:.2f} USD) ---")
    try:
        account_info = get_account_details_with_retry(client)
        assets_with_balance = False 
        if account_info and 'balances' in account_info: 
            for balance in account_info['balances']:
                asset = balance['asset']
                free_balance = float(balance['free'])
                locked_balance = float(balance['locked'])
                total_asset_balance = free_balance + locked_balance

                if total_asset_balance > 0:
                    price_in_usd = get_price_in_usd(asset, client) 
                    asset_value_in_usd = 0.0 
                    if price_in_usd is not None:
                         asset_value_in_usd = total_asset_balance * price_in_usd
                    
                    if price_in_usd is not None and asset_value_in_usd < dust_threshold:
                        total_dust_value_usd += asset_value_in_usd
                        logging.debug(f"Актив {asset} ({total_asset_balance:.8f}, ~{asset_value_in_usd:.4f} USD) відфільтровано як пил.")
                        continue 

                    assets_with_balance = True 
                    if price_in_usd is not None: 
                        total_spot_value_usd += asset_value_in_usd

                    spot_balances_list.append({
                        'Актив': asset,
                        'Вільний': free_balance,
                        'Заблокований': locked_balance,
                        'Всього': total_asset_balance,
                        'Вартість (USD)': asset_value_in_usd if price_in_usd is not None else None
                    })
            if not assets_with_balance and not spot_balances_list: 
                logging.info("На спотовому гаманці немає активів з балансом > 0 (після фільтрації пилу).")
        else:
            logging.error("Не вдалося отримати деталі акаунту або 'balances' відсутні у відповіді.")
            return [], 0.0, 0.0
        return spot_balances_list, total_spot_value_usd, total_dust_value_usd
    except Exception as e: 
        logging.error(f"Не вдалося отримати спотовий баланс після кількох спроб: {e}")
        return [], 0.0, 0.0

@retry_on_exception(allowed_exceptions_tuple=(BinanceAPIException, BinanceRequestException, ConnectionError, Timeout, TooManyRedirects))
def get_simple_earn_flexible_product_position_with_retry(client):
    return client.get_simple_earn_flexible_product_position()

@retry_on_exception(allowed_exceptions_tuple=(BinanceAPIException, BinanceRequestException, ConnectionError, Timeout, TooManyRedirects))
def get_simple_earn_locked_product_position_with_retry(client):
    return client.get_simple_earn_locked_product_position()

def get_earn_balance(client, dust_threshold=0.01):
    """
    Отримує баланс Binance Earn, фільтруючи "пил".
    Повертає список активів, їх загальну вартість та загальну вартість "пилу".
    """
    earn_balances_list = []
    total_earn_value_usd = 0.0
    total_dust_value_usd = 0.0

    logging.info(f"--- Отримання балансу Binance Earn (поріг пилу: {dust_threshold:.2f} USD) ---")
    try:
        # Flexible
        logging.info("  Спроба отримати Flexible Simple Earn...")
        flexible_response = get_simple_earn_flexible_product_position_with_retry(client)
        if flexible_response and 'rows' in flexible_response: 
            flexible_positions = flexible_response.get('rows', [])
            if flexible_positions:
                 logging.info(f"  Знайдено {len(flexible_positions)} Flexible Simple Earn позицій.")
                 for position in flexible_positions: 
                     asset = position.get('asset')
                     total_amount = float(position.get('totalAmount', 0))
                     if total_amount > 0 and asset: 
                         price_in_usd = get_price_in_usd(asset, client)
                         asset_value_in_usd = 0.0 
                         if price_in_usd is not None:
                              asset_value_in_usd = total_amount * price_in_usd
                         
                         if price_in_usd is not None and asset_value_in_usd < dust_threshold:
                             total_dust_value_usd += asset_value_in_usd
                             logging.debug(f"Earn актив {asset} (Flexible, {total_amount:.8f}, ~{asset_value_in_usd:.4f} USD) відфільтровано як пил.")
                             continue

                         if price_in_usd is not None: 
                            total_earn_value_usd += asset_value_in_usd
                         earn_balances_list.append({
                             'Актив': asset,
                             'Продукт': 'Flexible Simple Earn',
                             'Всього': total_amount,
                             'Вартість (USD)': asset_value_in_usd if price_in_usd is not None else None
                         })
            else:
                logging.info("  Не знайдено Flexible Simple Earn позицій з балансом > 0.")
        else:
            logging.warning("Не вдалося отримати дані Flexible Simple Earn або відповідь не містить 'rows'.")

        # Locked
        logging.info("  Спроба отримати Locked Simple Earn...")
        locked_response = get_simple_earn_locked_product_position_with_retry(client)
        if locked_response and 'rows' in locked_response: 
            locked_positions = locked_response.get('rows', [])
            if locked_positions:
                 logging.info(f"  Знайдено {len(locked_positions)} Locked Simple Earn позицій.")
                 for position in locked_positions: 
                     asset = position.get('asset')
                     total_amount = float(position.get('totalAmount', 0))
                     end_date = position.get('endDate')
                     if total_amount > 0 and asset: 
                          price_in_usd = get_price_in_usd(asset, client)
                          asset_value_in_usd = 0.0 
                          if price_in_usd is not None:
                               asset_value_in_usd = total_amount * price_in_usd

                          if price_in_usd is not None and asset_value_in_usd < dust_threshold:
                              total_dust_value_usd += asset_value_in_usd
                              logging.debug(f"Earn актив {asset} (Locked, {total_amount:.8f}, ~{asset_value_in_usd:.4f} USD) відфільтровано як пил.")
                              continue
                          
                          if price_in_usd is not None: 
                            total_earn_value_usd += asset_value_in_usd
                          earn_item = {
                              'Актив': asset,
                              'Продукт': 'Locked Simple Earn',
                              'Всього': total_amount,
                              'Вартість (USD)': asset_value_in_usd if price_in_usd is not None else None
                          }
                          if end_date:
                              earn_item['Дата закінчення'] = end_date 
                          earn_balances_list.append(earn_item)
            else:
                 logging.info("  Не знайдено Locked Simple Earn позицій з балансом > 0.")
        else:
            logging.warning("Не вдалося отримати дані Locked Simple Earn або відповідь не містить 'rows'.")

        if not earn_balances_list and total_dust_value_usd == 0: 
             logging.info("На рахунку Binance Earn немає активів з балансом > 0 (після фільтрації пилу).")
        return earn_balances_list, total_earn_value_usd, total_dust_value_usd
    except Exception as e: 
        logging.error(f"Не вдалося отримати Earn баланс після кількох спроб: {e}")
        import traceback
        logging.error("Деталі помилки:")
        logging.error(traceback.format_exc())
        return [], 0.0, 0.0

@retry_on_exception(allowed_exceptions_tuple=(BinanceAPIException, BinanceRequestException, ConnectionError, Timeout, TooManyRedirects))
def get_futures_usdt_account_details_with_retry(client): # Перейменовано для ясності
    return client.futures_account() 

def get_futures_balance(client): # Для USDT-M
    futures_total_usdt = 0.0
    futures_usdt_info = None
    logging.info("--- Отримання балансу USDT-M ф'ючерсів ---")
    try:
        futures_account_info = get_futures_usdt_account_details_with_retry(client) # Використовуємо нову назву
        usdt_info_found = False
        if futures_account_info and 'assets' in futures_account_info: 
            for asset_info in futures_account_info['assets']:
                 if asset_info['asset'] == 'USDT':
                     usdt_info_found = True
                     wallet_balance = float(asset_info['walletBalance'])
                     unrealized_pnl = float(asset_info['unrealizedProfit'])
                     futures_total_usdt = wallet_balance + unrealized_pnl
                     logging.info(f"Актив: {asset_info['asset']} (USDT-M)")
                     logging.info(f"  Баланс гаманця: {wallet_balance:.8f}")
                     logging.info(f"  Нереалізований PNL: {unrealized_pnl:.8f}")
                     logging.info(f"  Загальний баланс активу (в USDT): {futures_total_usdt:.8f}")
                     futures_usdt_info = {
                         'Актив': asset_info['asset'],
                         'Баланс гаманця': wallet_balance,
                         'Нереалізований PNL': unrealized_pnl,
                         'Загалом (USDT)': futures_total_usdt
                     }
                     break
            if not usdt_info_found:
                 logging.info("Інформація про актив USDT на USDT-M ф'ючерсному гаманці не знайдена.")
        else:
            logging.error("Не вдалося отримати деталі USDT-M ф'ючерсного акаунту або 'assets' відсутні у відповіді.")
            return 0.0, None 
        return futures_total_usdt, futures_usdt_info
    except Exception as e: 
        logging.error(f"Не вдалося отримати USDT-M ф'ючерсний баланс після кількох спроб: {e}")
        if isinstance(e, BinanceAPIException) and \
           ("Margin is not enabled" in str(e) or \
            "You don't have permission" in str(e) or \
            "Invalid API-key, IP, or permissions" in str(e)):
             logging.error("Можливо, у вас не активований USDT-M ф'ючерсний акаунт або API ключ не має дозволу на ф'ючерси.")
        return 0.0, None

@retry_on_exception(allowed_exceptions_tuple=(BinanceAPIException, BinanceRequestException, ConnectionError, Timeout, TooManyRedirects))
def get_futures_coin_account_details_with_retry(client):
    """Отримує деталі COIN-M ф'ючерсного акаунту з retry."""
    return client.futures_coin_account() 

def get_coin_m_futures_balance(client):
    """
    Отримує баланс COIN-M ф'ючерсів та розраховує його загальну вартість у USD.
    Повертає список активів та їх загальну вартість.
    """
    coin_m_balances_list = []
    total_coin_m_value_usd = 0.0
    logging.info("--- Отримання балансу COIN-M ф'ючерсів ---")

    try:
        account_info = get_futures_coin_account_details_with_retry(client)
        
        if not account_info or 'assets' not in account_info:
            logging.error("Не вдалося отримати деталі COIN-M ф'ючерсного акаунту або ключ 'assets' відсутній у відповіді.")
            return [], 0.0

        logging.debug(f"COIN-M account_info raw: {account_info}") 

        assets_data = account_info.get('assets', []) 

        for asset_data in assets_data:
            asset_symbol = asset_data.get('asset')
            wallet_balance_str = asset_data.get('walletBalance')
            unrealized_pnl_str = asset_data.get('unrealizedProfit')

            if not asset_symbol or wallet_balance_str is None or unrealized_pnl_str is None:
                logging.warning(f"Пропуск активу в COIN-M через відсутність обов'язкових полів: {asset_data}")
                continue

            try:
                wallet_balance = float(wallet_balance_str)
                unrealized_pnl = float(unrealized_pnl_str)
            except ValueError:
                logging.error(f"Не вдалося конвертувати фінансові показники у число для {asset_symbol} в COIN-M: {asset_data}")
                continue
            
            total_asset_coin_balance = wallet_balance + unrealized_pnl

            # Обробляємо активи, де є хоча б якийсь значущий баланс гаманця або PNL
            # Використовуємо мале число для порівняння з плаваючою точкою, щоб уникнути проблем з точністю
            if abs(wallet_balance) > 1e-9 or abs(unrealized_pnl) > 1e-9 or abs(total_asset_coin_balance) > 1e-9:
                price_in_usd = get_price_in_usd(asset_symbol, client)
                asset_value_in_usd = 0.0 
                
                if price_in_usd is not None:
                    asset_value_in_usd = total_asset_coin_balance * price_in_usd
                    total_coin_m_value_usd += asset_value_in_usd
                else:
                    logging.warning(f"Не вдалося отримати ціну в USD для {asset_symbol} (COIN-M). Вартість цього активу не буде врахована у підсумку.")

                coin_m_balances_list.append({
                    'Актив': asset_symbol,
                    'Баланс гаманця': wallet_balance,
                    'Нереалізований PNL': unrealized_pnl,
                    'Загалом в монеті': total_asset_coin_balance, 
                    'Ціна (USD)': price_in_usd, 
                    'Вартість (USD)': asset_value_in_usd if price_in_usd is not None else None
                })
                logging.info(f"  COIN-M Актив: {asset_symbol}, Гаманець: {wallet_balance:.8f}, PNL: {unrealized_pnl:.8f}, Всього: {total_asset_coin_balance:.8f} {asset_symbol}, "
                             f"Оцінка USD: {'{:.2f}'.format(asset_value_in_usd) if price_in_usd is not None else 'N/A'} USD (Ціна: {'{:.2f}'.format(price_in_usd) if price_in_usd is not None else 'N/A'} USD)")

        if not coin_m_balances_list:
            logging.info("На COIN-M ф'ючерсному рахунку немає активів з значущим балансом/PNL для відображення.")
            
    except BinanceAPIException as e:
        logging.error(f"Помилка Binance API при отриманні балансу COIN-M ф'ючерсів: {e}")
        if "This account is not a COIN-M account" in str(e) or e.code == -2015: 
             logging.error("Цей акаунт не є COIN-M ф'ючерсним акаунтом або API ключ не має відповідних дозволів.")
        return [], 0.0
    except Exception as e:
        logging.error(f"Невідома помилка при отриманні балансу COIN-M ф'ючерсів: {e}")
        import traceback
        logging.error("Деталі помилки:")
        logging.error(traceback.format_exc())
        return [], 0.0
        
    return coin_m_balances_list, total_coin_m_value_usd