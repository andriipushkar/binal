import pytest
from unittest.mock import MagicMock
from balance.account import BinanceAccount

@pytest.fixture
def mock_binance_client(mocker):
    """
    Створюємо "фікстуру" - підготовлений об'єкт, який буде
    імітувати справжній клієнт Binance API.
    """
    mock_client = MagicMock()
    
    # Готуємо фейкову відповідь від API для балансів
    mock_client.get_account.return_value = {
        'balances': [
            {'asset': 'BTC', 'free': '1.0', 'locked': '0.5'},
            {'asset': 'ETH', 'free': '10.0', 'locked': '5.0'},
            {'asset': 'LTC', 'free': '0.1', 'locked': '0.0'}, # Цей актив буде "пилом"
        ]
    }
    
    # Готуємо фейкові відповіді для цін
    # side_effect дозволяє повертати різні значення при кожному виклику
    mock_client.get_symbol_ticker.side_effect = [
        {'price': '60000.0'}, # Ціна для BTCUSDT
        {'price': '3000.0'},  # Ціна для ETHUSDT
        {'price': '100.0'},   # Ціна для LTCUSDT
    ]
    
    # "Патчимо" - тимчасово замінюємо справжній Client на наш мок
    mocker.patch('balance.account.Client', return_value=mock_client)
    return mock_client

def test_get_spot_balance_with_mock(mock_binance_client):
    """
    Тестуємо метод get_spot_balance, використовуючи наш імітований клієнт.
    """
    # Створюємо екземпляр класу. Ключі не мають значення, бо клієнт імітований.
    account = BinanceAccount(api_key="test_key", secret_key="test_secret")
    account.client = mock_binance_client # Явно встановлюємо наш мок

    # Викликаємо метод, який хочемо протестувати
    spot_list, total_usd, dust_usd = account.get_spot_balance(dust_threshold=15.0)

    # Перевіряємо, чи правильно все пораховано
    # 1.5 BTC * 60000 + 15 ETH * 3000 = 90000 + 45000 = 135000
    assert total_usd == pytest.approx(135000.0) 
    # 0.1 LTC * 100 = 10.0 (менше за поріг пилу 15.0)
    assert dust_usd == pytest.approx(10.0)

    # Перевіряємо, що LTC було відфільтровано
    asset_names = [item['Актив'] for item in spot_list]
    assert 'LTC' not in asset_names
    assert len(spot_list) == 2

def test_get_earn_balance_with_mock(mock_binance_client):
    """
    Тестує метод get_earn_balance з використанням мока.
    """
    # Мокуємо відповіді для Earn
    mock_binance_client.get_simple_earn_flexible_product_position.return_value = {
        'rows': [
            {'asset': 'USDT', 'totalAmount': '100.0'},
        ]
    }
    mock_binance_client.get_simple_earn_locked_product_position.return_value = {
        'rows': [
            {'asset': 'BTC', 'totalAmount': '0.1'},
        ]
    }

    # Створюємо екземпляр класу
    account = BinanceAccount(api_key="test_key", secret_key="test_secret")
    account.client = mock_binance_client

    # Мокуємо ціни для активів в Earn
    account.price_cache = {'USDT': 1.0, 'BTC': 60000.0}

    earn_list, total_usd, dust_usd = account.get_earn_balance(dust_threshold=0.01)

    # Перевіряємо загальні суми
    assert total_usd == pytest.approx(100.0 * 1.0 + 0.1 * 60000.0)
    assert dust_usd == 0.0

    # Перевіряємо, що активи є у списку
    asset_names = [item['Актив'] for item in earn_list]
    assert 'USDT' in asset_names
    assert 'BTC' in asset_names
    assert len(earn_list) == 2

def test_get_futures_balance_with_mock(mock_binance_client):
    """
    Тестує метод get_futures_balance (USDT-M) з використанням мока.
    """
    # Мокуємо відповідь для USDT-M Futures
    mock_binance_client.futures_account.return_value = {
        'assets': [
            {'asset': 'USDT', 'walletBalance': '1000.0', 'unrealizedProfit': '50.0'},
        ]
    }

    account = BinanceAccount(api_key="test_key", secret_key="test_secret")
    account.client = mock_binance_client

    total_usd, futures_info = account.get_futures_balance()

    assert total_usd == pytest.approx(1050.0)
    assert futures_info['Актив'] == 'USDT'

def test_get_coin_m_futures_balance_with_mock(mock_binance_client):
    """
    Тестує метод get_coin_m_futures_balance з використанням мока.
    """
    # Мокуємо відповідь для COIN-M Futures
    mock_binance_client.futures_coin_account.return_value = {
        'assets': [
            {'asset': 'BTC', 'walletBalance': '2.0', 'unrealizedProfit': '-0.1'},
        ]
    }

    account = BinanceAccount(api_key="test_key", secret_key="test_secret")
    account.client = mock_binance_client
    account.price_cache = {'BTC': 60000.0}

    coin_m_list, total_usd = account.get_coin_m_futures_balance()

    assert total_usd == pytest.approx(1.9 * 60000.0)
    assert len(coin_m_list) == 1
    assert coin_m_list[0]['Актив'] == 'BTC'
