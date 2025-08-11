import pandas as pd
import matplotlib.pyplot as plt
import os
import logging

def plot_balance_history(history_file_path, output_image_path):
    """
    Читає історію балансу з CSV файлу та генерує графік.
    """
    try:
        if not os.path.exists(history_file_path):
            logging.warning(f"Файл історії '{history_file_path}' не знайдено. Графік не буде створено.")
            return

        df = pd.read_csv(history_file_path)

        if df.empty:
            logging.warning(f"Файл історії '{history_file_path}' порожній. Графік не буде створено.")
            return

        # Перетворюємо колонку 'timestamp' у формат дати
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        plt.figure(figsize=(12, 6))
        plt.plot(df['timestamp'], df['total_balance_usd'], marker='o', linestyle='-')
        
        plt.title('Історія Загального Балансу (USD)')
        plt.xlabel('Дата')
        plt.ylabel('Загальний Баланс (USD)')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.savefig(output_image_path)
        logging.info(f"Графік історії балансу збережено: {output_image_path}")

    except Exception as e:
        logging.error(f"Помилка при створенні графіку: {e}")

if __name__ == '__main__':
    # Для самостійного тестування
    # Переконуємось, що ми працюємо з кореневої папки проекту
    # Це для прикладу, основний виклик буде з main.py
    from balance.config import OUTPUT_DIR
    history_file = os.path.join(OUTPUT_DIR, 'balance_history.csv')
    output_image = os.path.join(OUTPUT_DIR, 'history_chart.png')
    plot_balance_history(history_file, output_image)
