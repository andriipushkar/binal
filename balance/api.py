import os
import logging
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Припустимо, логування вже налаштовано в головному скрипті (main.py або зовнішньому)
# Функції тут просто використовують існуючий логер

# Кеш цін оголошений на рівні модуля api
price_cache = {}

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

def get_price_in_usd(symbol, client):
    """
    Отримує поточну оціночну ціну символу у парі з USDT, BUSD, BTC або BNB (з кешуванням).
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
        btc_usdt_price = get_price_in_usd('BTC', client) # Рекурсивний виклик

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

    logging.info("--- Отримання спотового балансу ---")
    try:
        account_info = client.get_account()

        assets_with_balance = False
        for balance in account_info['balances']:
            asset = balance['asset']
            free_balance = float(balance['free'])
            locked_balance = float(balance['locked'])
            total_asset_balance = free_balance + locked_balance

            # Включаємо в список лише активи з ненульовим балансом
            if total_asset_balance > 0:
                assets_with_balance = True

                asset_value_in_usd = 0
                price_in_usd = get_price_in_usd(asset, client) # Передаємо client

                if price_in_usd is not None:
                     asset_value_in_usd = total_asset_balance * price_in_usd
                     total_spot_value_usd += asset_value_in_usd

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

# !!! ФІНАЛЬНА ВИПРАВЛЕНА ФУНКЦІЯ ДЛЯ ОТРИМАННЯ EARN БАЛАНСУ !!!
def get_earn_balance(client):
    """Отримує баланс рахунку Binance Earn (Simple Earn: Flexible, Locked)."""
    earn_balances_list = []
    total_earn_value_usd = 0.0

    logging.info("--- Отримання балансу Binance Earn (Simple Earn) ---")
    try:
        # Спробуємо отримати Flexible Simple Earn позиції
        logging.info("  Спроба отримати Flexible Simple Earn...")
        flexible_response = client.get_simple_earn_flexible_product_position() # Отримуємо словник
        # !!! ВИПРАВЛЕНО: Безпечно отримуємо список позицій під ключем 'rows'
        flexible_positions = flexible_response.get('rows', []) 

        if flexible_positions:
             logging.info(f"  Знайдено {len(flexible_positions)} Flexible Simple Earn позицій з балансом > 0.") # Уточнено лог
             for position in flexible_positions: # Тепер 'position' буде словником
                 asset = position.get('asset')
                 total_amount = float(position.get('totalAmount', 0))

                 if total_amount > 0 and asset: # Перевіряємо, що актив існує і баланс > 0
                     asset_value_in_usd = 0
                     price_in_usd = get_price_in_usd(asset, client)

                     if price_in_usd is not None:
                          asset_value_in_usd = total_amount * price_in_usd
                          total_earn_value_usd += asset_value_in_usd

                     earn_balances_list.append({
                         'Актив': asset,
                         'Продукт': 'Flexible Simple Earn',
                         'Всього': total_amount,
                         'Вартість (USD)': asset_value_in_usd if price_in_usd is not None else None
                     })
        else:
            logging.info("  Не знайдено Flexible Simple Earn позицій з балансом > 0.") # Змінено текст


        # Спробуємо отримати Locked Simple Earn позиції
        logging.info("  Спроба отримати Locked Simple Earn...")
        locked_response = client.get_simple_earn_locked_product_position() # Цей метод теж повертає словник
        # !!! ВИПРАВЛЕНО: Безпечно отримуємо список позицій під ключем 'rows'
        locked_positions = locked_response.get('rows', [])


        if locked_positions:
             logging.info(f"  Знайдено {len(locked_positions)} Locked Simple Earn позицій з балансом > 0.") # Уточнено лог
             for position in locked_positions: # 'position' тут буде словником
                 asset = position.get('asset')
                 total_amount = float(position.get('totalAmount', 0))
                 end_date = position.get('endDate')

                 if total_amount > 0 and asset: # Перевіряємо, що актив існує і баланс > 0
                      asset_value_in_usd = 0
                      price_in_usd = get_price_in_usd(asset, client)

                      if price_in_usd is not None:
                           asset_value_in_usd = total_amount * price_in_usd
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
             logging.info("  Не знайдено Locked Simple Earn позицій з балансом > 0.") # Змінено текст


        if not earn_balances_list:
             logging.info("На рахунку Binance Earn немає активів з балансом > 0 (або не знайдено підтримуваних Simple Earn продуктів).")

        return earn_balances_list, total_earn_value_usd

    except BinanceAPIException as e:
        logging.error(f"Помилка Binance API при отриманні балансу Binance Earn: {e}")
        if "You don't have permission" in str(e) or "Product does not exist" in str(e) or "Invalid API-key, IP, or permissions" in str(e):
             logging.error("Можливо, API ключ не має дозволу на Earn або у вас немає активних продуктів Earn.")
        return [], 0.0
    except Exception as e:
        logging.error(f"Невідома помишка при отриманні балансу Binance Earn: {e}")
        # Деталі помилки: логуємо трасування для будь-яких інших помилок
        import traceback
        logging.error("Деталі помилки:")
        logging.error(traceback.format_exc())

        return [], 0.0

# Решта коду файлу balance/api.py залишається без змін

def get_futures_balance(client):
    """Отримує ф'ючерсний баланс USDT-M."""
    futures_total_usdt = 0.0
    futures_usdt_info = None

    logging.info("--- Отримання ф'ючерсного балансу (USDT-M) ---")
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

                 futures_usdt_info = {
                     'Актив': asset_info['asset'],
                     'Баланс гаманця': wallet_balance,
                     'Нереалізований PNL': unrealized_pnl,
                     'Загалом (USDT)': futures_total_usdt
                 }

                 break

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

# Блок if __name__ == "__main__": відсутній в модулях пакету