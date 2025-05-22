from balance import script_runner, config

if __name__ == "__main__":
    config.setup_logging("_futures_report")
    script_runner.run_balance_script("futures", "futures_account_binance.py")