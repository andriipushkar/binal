from balance import script_runner, config

if __name__ == "__main__":
    config.setup_logging("_earn_report")
    script_runner.run_balance_script("earn", "earn_account_binance.py")