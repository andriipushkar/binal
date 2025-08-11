# balance/account.py
import logging
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

def retry_on_exception(retries=3, delay=5, allowed_exceptions_tuple=None):
    """
    Декоратор для повторного виконання функції у разі виникнення певних винятків.
    """
    if allowed_exceptions_tuple is None:
        effective_allowed_exceptions = (
            BinanceRequestException,
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
                    if e_api.code == -1121 and "Invalid symbol" in str(e_api):
                        raise
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
                except effective_allowed_exceptions as e_net:
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
            return None
        return wrapper
    return decorator

class BinanceAccount:
    """
    Клас для представлення акаунту Binance та взаємодії з ним.
    Інкапсулює клієнт API та логіку роботи з ним.
    """
    def __init__(self, api_key: str, secret_key: str):
        """
        Ініціалізує акаунт з API ключами та створює клієнт.
        """
        if not api_key or not secret_key:
            raise ValueError("API ключ та секретний ключ не можуть бути порожніми.")
            
        self.api_key = api_key
        self.secret_key = secret_key
        self.client = self._initialize_client()
        self.price_cache = {}

    def _initialize_client(self) -> Client | None:
        """
        Приватний метод для ініціалізації та перевірки клієнта Binance API.
        """
        try:
            client = Client(self.api_key, self.secret_key)
            client.ping()
            logging.info("Успішно підключено до Binance API.")
            return client
        except BinanceAPIException as e:
            logging.error(f"Помилка Binance API під час ініціалізації клієнта: {e}")
            return None
        except Exception as e:
            logging.error(f"Загальна помилка під час ініціалізації клієнта: {e}")
            return None

    @retry_on_exception(retries=3, delay=2, allowed_exceptions_tuple=(BinanceAPIException, BinanceRequestException, ConnectionError, Timeout, TooManyRedirects))
    def _get_ticker_price_raw(self, symbol_pair):
        """
        Базова функція для отримання ціни, до якої застосовується retry.
        """
        ticker = self.client.get_symbol_ticker(symbol=symbol_pair)
        return float(ticker['price'])

    def _try_get_price_via_stablecoin(self, symbol, stablecoin):
        stablecoin_symbol = f"{symbol}{stablecoin}"
        try:
            price = self._get_ticker_price_raw(stablecoin_symbol)
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

    def _try_get_price_via_conversion(self, symbol, conversion_asset): 
        pair_symbol = f"{symbol}{conversion_asset}"
        try:
            price_in_conversion_asset = self._get_ticker_price_raw(pair_symbol)
            conversion_asset_usd_price = self.get_price_in_usd(conversion_asset) 
            if conversion_asset_usd_price > 0:
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

    def get_price_in_usd(self, symbol):
        """
        Отримує поточну оціночну ціну символу в USD.
        """
        if symbol in self.price_cache:
            return self.price_cache[symbol]

        if symbol in ['USDT', 'BUSD', 'USDC', 'TUSD', 'DAI', 'USD']:
            self.price_cache[symbol] = 1.0
            return 1.0

        logging.debug(f"Пошук ціни для {symbol}...")

        stablecoins_to_try = ['USDT', 'BUSD', 'USDC', 'TUSD']
        for stablecoin in stablecoins_to_try:
            price = self._try_get_price_via_stablecoin(symbol, stablecoin)
            if price is not None:
                self.price_cache[symbol] = price
                return price

        price = self._try_get_price_via_conversion(symbol, 'BTC')
        if price is not None:
            self.price_cache[symbol] = price
            return price

        price = self._try_get_price_via_conversion(symbol, 'BNB')
        if price is not None:
            self.price_cache[symbol] = price
            return price
        
        logging.error(f"ПОВНА ПОМИЛКА: Не вдалося отримати ціну для '{symbol}' жодним зі способів.")
        self.price_cache[symbol] = 0.0
        return 0.0

    @retry_on_exception()
    def get_spot_balance(self, dust_threshold=0.01):
        spot_balances_list = []
        total_spot_value_usd = 0.0
        total_dust_value_usd = 0.0
        account_info = self.client.get_account()
        if account_info and 'balances' in account_info:
            for balance in account_info['balances']:
                asset = balance['asset']
                free_balance = float(balance['free'])
                locked_balance = float(balance['locked'])
                total_asset_balance = free_balance + locked_balance
                if total_asset_balance > 0:
                    price_in_usd = self.get_price_in_usd(asset)
                    asset_value_in_usd = 0.0
                    if price_in_usd > 0:
                        asset_value_in_usd = total_asset_balance * price_in_usd
                    if price_in_usd > 0 and asset_value_in_usd < dust_threshold:
                        total_dust_value_usd += asset_value_in_usd
                        continue
                    if price_in_usd > 0:
                        total_spot_value_usd += asset_value_in_usd
                    spot_balances_list.append({
                        'Актив': asset,
                        'Вільний': free_balance,
                        'Заблокований': locked_balance,
                        'Всього': total_asset_balance,
                        'Вартість (USD)': asset_value_in_usd if price_in_usd > 0 else "N/A"
                    })
        return spot_balances_list, total_spot_value_usd, total_dust_value_usd

    @retry_on_exception()
    def get_earn_balance(self, dust_threshold=0.01):
        earn_balances_list = []
        total_earn_value_usd = 0.0
        total_dust_value_usd = 0.0
        # Flexible
        flexible_response = self.client.get_simple_earn_flexible_product_position()
        if flexible_response and 'rows' in flexible_response:
            for position in flexible_response.get('rows', []):
                asset = position.get('asset')
                total_amount = float(position.get('totalAmount', 0))
                if total_amount > 0 and asset:
                    price_in_usd = self.get_price_in_usd(asset)
                    asset_value_in_usd = 0.0
                    if price_in_usd > 0:
                        asset_value_in_usd = total_amount * price_in_usd
                    if price_in_usd > 0 and asset_value_in_usd < dust_threshold:
                        total_dust_value_usd += asset_value_in_usd
                        continue
                    if price_in_usd > 0:
                        total_earn_value_usd += asset_value_in_usd
                    earn_balances_list.append({
                        'Актив': asset,
                        'Продукт': 'Flexible Simple Earn',
                        'Всього': total_amount,
                        'Вартість (USD)': asset_value_in_usd if price_in_usd > 0 else "N/A"
                    })
        # Locked
        locked_response = self.client.get_simple_earn_locked_product_position()
        if locked_response and 'rows' in locked_response:
            for position in locked_response.get('rows', []):
                asset = position.get('asset')
                total_amount = float(position.get('totalAmount', 0))
                end_date = position.get('endDate')
                if total_amount > 0 and asset:
                    price_in_usd = self.get_price_in_usd(asset)
                    asset_value_in_usd = 0.0
                    if price_in_usd > 0:
                        asset_value_in_usd = total_amount * price_in_usd
                    if price_in_usd > 0 and asset_value_in_usd < dust_threshold:
                        total_dust_value_usd += asset_value_in_usd
                        continue
                    if price_in_usd > 0:
                        total_earn_value_usd += asset_value_in_usd
                    earn_item = {
                        'Актив': asset,
                        'Продукт': 'Locked Simple Earn',
                        'Всього': total_amount,
                        'Вартість (USD)': asset_value_in_usd if price_in_usd > 0 else "N/A"
                    }
                    if end_date:
                        earn_item['Дата закінчення'] = end_date
                    earn_balances_list.append(earn_item)
        return earn_balances_list, total_earn_value_usd, total_dust_value_usd

    @retry_on_exception()
    def get_futures_balance(self):
        futures_total_usdt = 0.0
        futures_usdt_info = None
        futures_account_info = self.client.futures_account()
        if futures_account_info and 'assets' in futures_account_info:
            for asset_info in futures_account_info['assets']:
                if asset_info['asset'] == 'USDT':
                    wallet_balance = float(asset_info['walletBalance'])
                    unrealized_pnl = float(asset_info['unrealizedProfit'])
                    futures_total_usdt = wallet_balance + unrealized_pnl
                    futures_usdt_info = {
                        'Актив': asset_info['asset'],
                        'Баланс гаманця': wallet_balance,
                        'Нереалізований PNL': unrealized_pnl,
                        'Загалом (USDT)': futures_total_usdt
                    }
                    break
        return futures_total_usdt, futures_usdt_info

    @retry_on_exception()
    def get_coin_m_futures_balance(self):
        coin_m_balances_list = []
        total_coin_m_value_usd = 0.0
        account_info = self.client.futures_coin_account()
        if account_info and 'assets' in account_info:
            for asset_data in account_info.get('assets', []):
                asset_symbol = asset_data.get('asset')
                wallet_balance = float(asset_data.get('walletBalance'))
                unrealized_pnl = float(asset_data.get('unrealizedProfit'))
                total_asset_coin_balance = wallet_balance + unrealized_pnl
                if abs(total_asset_coin_balance) > 1e-9:
                    price_in_usd = self.get_price_in_usd(asset_symbol)
                    asset_value_in_usd = 0.0
                    if price_in_usd > 0:
                        asset_value_in_usd = total_asset_coin_balance * price_in_usd
                        total_coin_m_value_usd += asset_value_in_usd
                    coin_m_balances_list.append({
                        'Актив': asset_symbol,
                        'Баланс гаманця': wallet_balance,
                        'Нереалізований PNL': unrealized_pnl,
                        'Загалом в монеті': total_asset_coin_balance,
                        'Ціна (USD)': price_in_usd if price_in_usd > 0 else "N/A",
                        'Вартість (USD)': asset_value_in_usd if price_in_usd > 0 else "N/A"
                    })
        return coin_m_balances_list, total_coin_m_value_usd
