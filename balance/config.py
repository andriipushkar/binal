# pro1/balance/config.py
import os
import logging
from datetime import datetime

# --- Визначення шляхів відносно директорії пакета balance ---
# Директорія, де знаходиться цей файл config.py (тобто balance/)
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
# Коренева директорія проєкту (на один рівень вище від balance/)
PROJECT_ROOT_DIR = os.path.dirname(PACKAGE_DIR)

SERVICE_DIR = os.path.join(PROJECT_ROOT_DIR, 'service')
DOTENV_PATH = os.path.join(SERVICE_DIR, '.env')

# Папки logs та output всередині пакета balance
LOG_DIR = os.path.join(PACKAGE_DIR, 'logs')
OUTPUT_DIR = os.path.join(PACKAGE_DIR, 'output')

_LOGGING_INITIALIZED = False # Прапорець, що показує, чи було вже налаштовано логування

def setup_logging(log_file_suffix='_general'):
    """
    Налаштовує логування.
    Використовує LOG_DIR для збереження файлів логів.
    Додає суфікс до імені файлу логу для розрізнення.
    Налаштовує обробники лише один раз за сесію.
    """
    global _LOGGING_INITIALIZED

    if _LOGGING_INITIALIZED:
        logging.debug(f"Логування вже було ініціалізовано. Поточний виклик setup_logging з суфіксом '{log_file_suffix}' не буде переналаштовувати обробники.")
        return

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file_name = f"{timestamp}{log_file_suffix}.log"
    log_file_path = os.path.join(LOG_DIR, log_file_name)

    # Видаляємо всі попередні обробники, щоб уникнути дублювання, якщо вони якось залишились
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        handler.close()

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                        handlers=[
                            logging.FileHandler(log_file_path, encoding='utf-8'),
                            logging.StreamHandler() # Вивід у консоль
                        ])
    
    _LOGGING_INITIALIZED = True
    logging.info(f"Логування налаштовано. Основний файл логу для цього запуску: {log_file_path}")

# Приклад виклику для тестування (можна видалити або закоментувати)
if __name__ == '__main__':
    print(f"Project Root Dir: {PROJECT_ROOT_DIR}")
    print(f"Package Dir: {PACKAGE_DIR}")
    print(f"Service Dir: {SERVICE_DIR}")
    print(f"Dotenv Path: {DOTENV_PATH}")
    print(f"Log Dir: {LOG_DIR}")
    print(f"Output Dir: {OUTPUT_DIR}")

    setup_logging("_config_test_1")
    logging.info("Перше тестове повідомлення з config.py")
    setup_logging("_config_test_2") # Цей виклик не має змінити файл логу
    logging.info("Друге тестове повідомлення з config.py, має бути в тому ж файлі.")