# Аналізатор Балансу Binance

Цей проект є набором скриптів на Python для отримання та аналізу балансу вашого акаунту на біржі Binance. Він збирає дані зі спотового, Earn, USDT-M та COIN-M ф'ючерсних гаманців, розраховує їх загальну вартість в USD та зберігає результати у форматах `.txt` та `.json`.

## Встановлення

1.  **Клонуйте репозиторій:**
    ```bash
    git clone https://github.com/andriipushkar/binal.git
    cd binal
    ```

2.  **Встановіть залежності:**
    Рекомендується використовувати віртуальне середовище.
    ```bash
    python -m venv venv
    source venv/bin/activate  # для Linux/macOS
    # venv\Scripts\activate    # для Windows
    ```
    Встановіть необхідні пакети:
    ```bash
    pip install -r requirements.txt
    ```

## Конфігурація

1.  **Створіть файл `.env`** у папці `service`.
2.  **Додайте ваші API ключі** від Binance у файл `.env`:
    ```
    BINANCE_API_KEY=ваш_api_ключ
    BINANCE_SECRET_KEY=ваш_секретний_ключ
    ```
    **Важливо:** Переконайтеся, що для API ключів увімкнено дозвіл на читання інформації зі спотового та ф'ючерсних гаманців.

## Використання

Скрипт запускається з командного рядка за допомогою `main.py` з аргументом `--type` для вказівки типу звіту.

*   **Повний звіт (за замовчуванням):**
    ```bash
    python main.py
    ```
    або
    ```bash
    python main.py --type full
    ```

*   **Тільки спотовий гаманець:**
    ```bash
    python main.py --type spot
    ```

*   **Тільки Earn гаманець:**
    ```bash
    python main.py --type earn
    ```

*   **Тільки USDT-M ф'ючерсний гаманець:**
    ```bash
    python main.py --type futures
    ```

*   **Тільки COIN-M ф'ючерсний гаманець:**
    ```bash
    python main.py --type coin_m_futures
    ```

Результати роботи скриптів зберігаються в папку `balance/output/`, а лог-файли — в `balance/logs/`.
