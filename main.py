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
    parser.add_argument(
        '--visualize',
        action='store_true',
        help="Згенерувати графік історії балансу."
    )
    args = parser.parse_args()

    report_type = args.type
    # Створюємо умовне ім'я для логування, щоб зберегти сумісність
    script_name_for_log = f"{report_type}_report.py" 

    # Налаштування логування
    config.setup_logging(f"_{report_type}_report")

    # Запуск відповідного звіту
    script_runner.run_balance_script(report_type, script_name_for_log)

    if args.visualize:
        from visualize import plot_balance_history
        from balance.config import OUTPUT_DIR
        import os
        history_file = os.path.join(OUTPUT_DIR, 'balance_history.csv')
        output_image = os.path.join(OUTPUT_DIR, 'history_chart.png')
        plot_balance_history(history_file, output_image)

if __name__ == "__main__":
    main()