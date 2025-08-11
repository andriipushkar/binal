import pandas as pd
from balance.data_processing import format_spot_balance_table

def test_format_spot_balance_table_basic():
    """
    Тестує базове форматування таблиці спотового балансу.
    """
    spot_data = [
        {'Актив': 'BTC', 'Вільний': 1.0, 'Заблокований': 0.5, 'Всього': 1.5, 'Вартість (USD)': 100000.0},
        {'Актив': 'ETH', 'Вільний': 10.0, 'Заблокований': 5.0, 'Всього': 15.0, 'Вартість (USD)': 30000.0}
    ]
    
    result_table = format_spot_balance_table(spot_data)
    
    # Перевіряємо, що ключові слова та значення є у відформатованій таблиці
    assert 'BTC' in result_table
    assert '1.50000000' in result_table
    assert '100000.00' in result_table
    assert 'ETH' in result_table
    assert '15.00000000' in result_table
    assert '30000.00' in result_table

def test_format_spot_balance_table_empty():
    """
    Тестує випадок, коли на вхід подається порожній список.
    """
    result = format_spot_balance_table([])
    assert result == "На спотовому гаманці немає активів з балансом > 0."

def test_format_spot_balance_table_no_price():
    """
    Тестує випадок, коли для активу немає ціни (передано 'N/A').
    """
    spot_data = [
        {'Актив': 'LUNA', 'Вільний': 100.0, 'Заблокований': 0.0, 'Всього': 100.0, 'Вартість (USD)': 'N/A'}
    ]
    
    result_table = format_spot_balance_table(spot_data)
    
    assert 'LUNA' in result_table
    assert '100.00000000' in result_table
    assert 'N/A' in result_table
