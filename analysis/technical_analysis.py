import pandas as pd
import pandas_ta as ta
from binance.client import Client
import logging

def get_historical_data(client, symbol, interval=Client.KLINE_INTERVAL_1DAY, limit=200):
    """
    Отримує історичні дані OHLCV для вказаного символу.
    """
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 
            'close_time', 'quote_asset_volume', 'number_of_trades', 
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # Конвертуємо потрібні колонки у числовий формат
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
            
        # Встановлюємо timestamp як індекс
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df[['open', 'high', 'low', 'close', 'volume']]
    except Exception as e:
        logging.error(f"Помилка при отриманні історичних даних для {symbol}: {e}")
        return None

def add_technical_indicators(df):
    """
    Додає до DataFrame набір технічних індикаторів за допомогою pandas_ta.
    """
    if df is None or df.empty:
        return None
        
    # Створюємо власну стратегію з індикаторами
    custom_strategy = ta.Strategy(
        name="My Custom Strategy",
        description="RSI, MACD, BBands, EMAs, etc.",
        ta=[
            {"kind": "rsi"},
            {"kind": "macd"},
            {"kind": "bbands", "length": 20, "std": 2},
            {"kind": "ema", "length": 50},
            {"kind": "ema", "length": 200},
            {"kind": "adx"},
            {"kind": "stoch"},
        ]
    )
    
    # Застосовуємо стратегію до DataFrame
    df.ta.strategy(custom_strategy)
    
    return df

def analyze_symbol(client, symbol):
    """
    Виконує повний аналіз символу: завантажує дані, розраховує індикатори
    та виводить останні значення.
    """
    logging.info(f"Починаю технічний аналіз для символу: {symbol}")
    
    # 1. Отримати історичні дані
    df = get_historical_data(client, symbol)
    
    if df is None:
        return
        
    # 2. Додати індикатори
    df_with_indicators = add_technical_indicators(df)
    
    if df_with_indicators is None:
        logging.error("Не вдалося розрахувати індикатори.")
        return
        
    # 3. Вивести останні значення
    last_row = df_with_indicators.iloc[-1]
    
    print(f"\n--- Технічний Аналіз для {symbol} (останні дані) ---")
    print(last_row.to_string())
    print("--- Кінець аналізу ---")
