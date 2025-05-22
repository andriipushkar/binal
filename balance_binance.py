from balance import script_runner, config

if __name__ == "__main__":
    config.setup_logging("_full_script_report") # Суфікс для balance_binance.py
    script_runner.run_balance_script("full", "balance_binance.py")