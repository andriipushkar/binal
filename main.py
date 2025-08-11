import argparse
from balance import script_runner, config

def main():
    """
    Головна функція для запуску скрипта збору балансу.
    Розбирає аргументи командного рядка для визначення типу звіту.
    """
    parser = argparse.ArgumentParser(
        description="Скрипт для отримання звітів про баланс з Binance."
    )
    parser.add_argument(
        '--type',
        type=str,
        default='full',
        choices=['full', 'spot', 'earn', 'futures', 'coin_m_futures'],
        help="Тип звіту для генерації. 'full' (за замовчуванням) - для повного звіту."
    )
    args = parser.parse_args()

    report_type = args.type
    # Створюємо умовне ім'я для логування, щоб зберегти сумісність
    script_name_for_log = f"{report_type}_report.py" 

    # Налаштування логування
    config.setup_logging(f"_{report_type}_report")

    # Запуск відповідного звіту
    script_runner.run_balance_script(report_type, script_name_for_log)

if __name__ == "__main__":
    main()
