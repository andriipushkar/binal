# pro1/balance/api.py
import os
import logging
from dotenv import load_dotenv

def load_api_keys(dotenv_file_path):
    """Завантажує API ключі зі змінних оточення або файлу .env за вказаним шляхом."""
    if not os.path.exists(dotenv_file_path):
        logging.error(f"Помилка: Файл .env не знайдено за шляхом: {os.path.abspath(dotenv_file_path)}")
        return None, None

    load_dotenv(dotenv_path=dotenv_file_path)
    api_key = os.environ.get('BINANCE_API_KEY')
    secret_key = os.environ.get('BINANCE_SECRET_KEY')

    if not api_key or not secret_key:
        logging.error("Помилка: API ключі не завантажено з .env файлу.")
        logging.error("Перевірте, чи встановлено змінні 'BINANCE_API_KEY' та 'BINANCE_SECRET_KEY' у файлі.")
        return None, None

    logging.info("API ключі завантажено.")
    return api_key, secret_key
