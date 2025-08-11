import argparse
from balance import script_runner, config
import logging
import os

def main():
    """
    Головна функція для запуску скрипта.
    Розбирає аргументи командного рядка для визначення дії.
    """
    parser = argparse.ArgumentParser(
        description="Скрипт для роботи з акаунтом Binance."
    )
    parser.add_argument(
        '--type',
        type=str,
        default=None,
        choices=['full', 'spot', 'earn', 'futures', 'coin_m_futures'],
        help="Тип звіту по балансу для генерації. Якщо не вказано, звіт не генерується."
    )
    parser.add_argument(
        '--visualize',
        action='store_true',
        help="Згенерувати графік історії балансу."
    )
    parser.add_argument(
        '--ta',
        type=str,
        help="Символ для технічного аналізу (наприклад, BTCUSDT)."
    )
    args = parser.parse_args()

    # Налаштування логування
    log_suffix = args.type if args.type else "main"
    config.setup_logging(f"_{log_suffix}_report")

    # --- Виконання Технічного Аналізу ---
    if args.ta:
        from analysis.technical_analysis import analyze_symbol
        from balance.account import BinanceAccount
        from balance.api import load_api_keys
        
        api_key, secret_key = load_api_keys(config.DOTENV_PATH)
        if api_key and secret_key:
            try:
                account = BinanceAccount(api_key, secret_key)
                if account.client:
                    analyze_symbol(account.client, args.ta.upper())
            except ValueError as e:
                logging.error(f"Помилка створення об'єкту BinanceAccount: {e}")
        else:
            logging.error("API ключі не знайдено, технічний аналіз неможливий.")

    # --- Генерація Звіту по Балансу ---
    if args.type:
        script_name_for_log = f"{args.type}_report.py"
        script_runner.run_balance_script(args.type, script_name_for_log)

    # --- Візуалізація ---
    if args.visualize:
        from analysis.visualize import plot_balance_history
        history_file = os.path.join(config.OUTPUT_DIR, 'balance_history.csv')
        output_image = os.path.join(config.OUTPUT_DIR, 'history_chart.png')
        plot_balance_history(history_file, output_image)

    # Якщо жоден з основних аргументів не надано
    if not args.type and not args.ta and not args.visualize:
        logging.info("Не вказано жодної дії. Використовуйте --type, --ta або --visualize. Додайте -h для допомоги.")


if __name__ == "__main__":
    main()
