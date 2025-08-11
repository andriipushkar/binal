import pandas as pd
import pandas_ta as ta
from binance.client import Client
import logging

def get_historical_data(client, symbol, interval=Client.KLINE_INTERVAL_1DAY, limit=300):
    """
    Отримує історичні дані OHLCV для вказаного символу.
    Збільшено ліміт до 300, щоб забезпечити достатньо даних для індикаторів.
    """
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 
            'close_time', 'quote_asset_volume', 'number_of_trades', 
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
            
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df[['open', 'high', 'low', 'close', 'volume']]
    except Exception as e:
        logging.error(f"Помилка при отриманні історичних даних для {symbol}: {e}")
        return None

def add_technical_indicators(df):
    """
    Додає до DataFrame розширений набір технічних індикаторів.
    """
    if df is None or df.empty:
        return None
        
    # Розширений список індикаторів
    custom_strategy = ta.Strategy(
        name="Comprehensive Analysis",
        description="A comprehensive set of technical indicators.",
        ta=[
            # Momentum Indicators
            {"kind": "rsi", "length": 14},
            {"kind": "macd", "fast": 12, "slow": 26, "signal": 9},
            {"kind": "stoch", "k": 14, "d": 3, "smooth_k": 3},
            {"kind": "willr", "length": 14},
            {"kind": "ao"},
            {"kind": "cci", "length": 20},
            {"kind": "roc", "length": 10},
            {"kind": "trix", "length": 15},
            {"kind": "cmo", "length": 14},
            {"kind": "kst"},
            {"kind": "coppock"},
            {"kind": "tsi"},
            {"kind": "uo"},
            # {"kind": "accel", "length": 5}, # Accelerator Oscillator - Not available in pandas-ta
            {"kind": "dpo"}, # Detrended Price Oscillator
            
            # Trend Indicators
            {"kind": "ema", "length": 20},
            {"kind": "ema", "length": 50},
            {"kind": "ema", "length": 200},
            {"kind": "sma", "length": 20},
            {"kind": "sma", "length": 50},
            {"kind": "sma", "length": 200},
            {"kind": "adx", "length": 14},
            {"kind": "aroon", "length": 14},
            {"kind": "vortex", "length": 14},
            {"kind": "psar"},
            {"kind": "ichimoku"},
            {"kind": "supertrend"}, # Supertrend
            
            # Volatility Indicators
            {"kind": "bbands", "length": 20, "std": 2},
            {"kind": "atr", "length": 14},
            {"kind": "stdev", "length": 20},
            {"kind": "donchian", "lower_length": 20, "upper_length": 20},

            # Volume Indicators
            {"kind": "obv"},
            {"kind": "cmf", "length": 20},
            {"kind": "mfi", "length": 14},
            {"kind": "vwap"},
        ]
    )
    
    df.ta.strategy(custom_strategy)
    
    return df

def analyze_symbol(client, symbol):
    """
    Виконує повний аналіз символу та виводить результат у структурованому вигляді.
    """
    logging.info(f"Починаю розширений технічний аналіз для символу: {symbol}")
    
    df = get_historical_data(client, symbol)
    if df is None:
        return
        
    df_with_indicators = add_technical_indicators(df)
    if df_with_indicators is None:
        logging.error("Не вдалося розрахувати індикатори.")
        return
        
    last_row = df_with_indicators.iloc[-1]
    
    # Групуємо індикатори для кращої читабельності
    momentum_indicators = ['RSI_14', 'MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9', 'STOCHk_14_3_3', 'STOCHd_14_3_3', 'WILLR_14', 'AO', 'CCI_20_0.015', 'ROC_10', 'TRIX_15_9', 'CMO_14', 'KST_10_15_20_30_10_10_10_15', 'KSTs_9', 'COPC_11_14_10', 'TSI_13_25_13', 'UOS_7_14_28', 'DPO_20']
    trend_indicators = ['EMA_20', 'EMA_50', 'EMA_200', 'SMA_20', 'SMA_50', 'SMA_200', 'ADX_14', 'AROOND_14', 'AROONU_14', 'AROONOSC_14', 'VORTEX_14_plus', 'VORTEX_14_minus', 'PSARl_0.02_0.2', 'PSARs_0.02_0.2', 'ITS_9', 'IKS_26', 'ISA_26', 'ISB_52', 'ICS_26', 'SUPERT_7_3.0', 'SUPERTd_7_3.0', 'SUPERTl_7_3.0', 'SUPERTs_7_3.0']
    volatility_indicators = ['BBL_20_2.0', 'BBM_20_2.0', 'BBU_20_2.0', 'BBB_20_2.0', 'BBP_20_2.0', 'ATRr_14', 'STDEV_20', 'DCL_20_20', 'DCM_20_20', 'DCU_20_20']
    volume_indicators = ['OBV', 'CMF_20', 'MFI_14', 'VWAP_D']

    print(f"\n--- Розширений Технічний Аналіз для {symbol} (останні дані) ---")
    print(f"Дата: {last_row.name.strftime('%Y-%m-%d')}")
    print(f"Ціна закриття: {last_row['close']:.2f}\n")

    def print_section(title, indicators):
        print(f"--- {title} ---")
        # Вибираємо тільки ті індикатори, які є в DataFrame
        valid_indicators = [ind for ind in indicators if ind in last_row.index]
        if valid_indicators:
            print(last_row[valid_indicators].to_string())
        else:
            print("Немає даних для цієї категорії.")
        print("")

    print_section("Індикатори Моментуму", momentum_indicators)
    print_section("Трендові Індикатори", trend_indicators)
    print_section("Індикатори Волатильності", volatility_indicators)
    print_section("Індикатори Об'єму", volume_indicators)
    
    print("--- Кінець аналізу ---")
