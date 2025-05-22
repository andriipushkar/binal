# pro1/balance/main.py
import logging
import argparse 
from . import config
from . import script_runner 

def main():
    parser = argparse.ArgumentParser(description="Отримання звітів про баланс Binance.")
    
    parser.add_argument(
        '--spot', 
        action='store_true',
        help="Отримати спотовий баланс."
    )
    parser.add_argument( # Змінимо назву для ясності, що це USDT-M
        '--usdtm', # Раніше було --futures
        action='store_true', 
        help="Отримати USDT-M ф'ючерсний баланс."
    )
    parser.add_argument(
        '--coinm', # Новий аргумент для COIN-M
        action='store_true',
        help="Отримати COIN-M ф'ючерсний баланс."
    )
    parser.add_argument(
        '--earn', 
        action='store_true', 
        help="Отримати Earn баланс."
    )
    parser.add_argument(
        '--full', 
        action='store_true', 
        help="Отримати повний звіт (спот, earn, USDT-M, COIN-M). Є поведінкою за замовчуванням."
    )
    parser.add_argument(
        '--dust-threshold',
        type=float,
        default=0.01, 
        help="Поріг для фільтрації 'пилу' в USD (для Spot та Earn). (За замовчуванням: 0.01)"
    )

    args = parser.parse_args()

    log_suffix_parts = ["_main_cli"] 
    requested_reports_for_log = []
    if args.spot: requested_reports_for_log.append("spot")
    if args.usdtm: requested_reports_for_log.append("usdtm") # Оновлено
    if args.coinm: requested_reports_for_log.append("coinm") # Додано
    if args.earn: requested_reports_for_log.append("earn")
    
    if args.full or not requested_reports_for_log:
        log_suffix_parts.append("full")
    else:
        log_suffix_parts.extend(requested_reports_for_log) 
    
    final_log_suffix = "_".join(log_suffix_parts)
    config.setup_logging(final_log_suffix) 

    logging.info(f"Розпочато виконання головного модуля balance.main з аргументами: {args}")
    logging.info(f"Файл логу для цього запуску буде мати суфікс: {final_log_suffix}")
    logging.info(f"Поріг для фільтрації 'пилу' встановлено на: {args.dust_threshold:.2f} USD")

    run_spot = args.spot
    run_usdtm_futures = args.usdtm # Оновлено
    run_coinm_futures = args.coinm # Додано
    run_earn = args.earn
    run_full = args.full
    dust_threshold = args.dust_threshold

    is_any_specific_report_requested = run_spot or run_usdtm_futures or run_coinm_futures or run_earn
    
    if run_full or not is_any_specific_report_requested:
        logging.info("Запускається генерація повного звіту про баланс.")
        script_runner.run_balance_script("full", "balance.main (модуль, повний звіт)", dust_threshold=dust_threshold)
    else:
        if run_spot:
            logging.info("Запускається генерація звіту про спотовий баланс.")
            script_runner.run_balance_script("spot", "balance.main (модуль, спот)", dust_threshold=dust_threshold)
        if run_usdtm_futures:
            logging.info("Запускається генерація звіту про USDT-M ф'ючерсний баланс.")
            # "futures" у script_runner тепер означає USDT-M
            script_runner.run_balance_script("futures", "balance.main (модуль, USDT-M ф'ючерси)") 
        if run_coinm_futures:
            logging.info("Запускається генерація звіту про COIN-M ф'ючерсний баланс.")
            script_runner.run_balance_script("coin_m_futures", "balance.main (модуль, COIN-M ф'ючерси)")
        if run_earn:
            logging.info("Запускається генерація звіту про Earn баланс.")
            script_runner.run_balance_script("earn", "balance.main (модуль, earn)", dust_threshold=dust_threshold)
            
    logging.info(f"Завершено виконання головного модуля balance.main.")

if __name__ == "__main__":
    main()