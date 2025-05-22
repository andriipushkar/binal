from balance import script_runner, config

if __name__ == "__main__":
    config.setup_logging("_spot_report") # Налаштовуємо лог для цього скрипта
    script_runner.run_balance_script("spot", "spot_account_binance.py")