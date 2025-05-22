# pro1/coin_m_futures_account_binance.py
from balance import script_runner, config

if __name__ == "__main__":
    config.setup_logging("_coin_m_futures_report") 
    # Припускаємо, що фільтр пилу не застосовується до COIN-M на рівні окремого скрипта,
    # або можна додати argparse сюди теж.
    script_runner.run_balance_script("coin_m_futures", "coin_m_futures_account_binance.py")