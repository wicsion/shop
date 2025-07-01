import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite3
from tqdm import tqdm
import logging
import psutil

# Проверка активации виртуального окружения
if 'VIRTUAL_ENV' not in os.environ:
    raise EnvironmentError("Virtual environment not activated!")

# Настройки
TOTAL_PRODUCTS = 17481
BATCH_SIZE = 3000
MAX_WORKERS = 5
DB_PATH = os.path.join(os.getcwd(), 'db.sqlite3')
PYTHON_EXEC = os.path.join(os.environ['VIRTUAL_ENV'], 'Scripts', 'python.exe')

# Настройка логов
logging.basicConfig(
    level=logging.WARNING,  # Было INFO
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import.log'),
        logging.StreamHandler()
    ]
)


def prepare_database():
    """Оптимизация SQLite для Windows"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Файл БД не найден: {DB_PATH}")

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = OFF")  # Было NORMAL
        conn.execute("PRAGMA cache_size = -20000")  # Было -10000
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.close()
        logging.info("Оптимизация БД выполнена")
    except Exception as e:
        logging.error(f"Ошибка оптимизации БД: {e}")
        raise


def run_import(offset):
    """Запуск импорта с активированным окружением"""
    try:
        cmd = [
            PYTHON_EXEC,
            'manage.py',
            'import_xml_products',
            f'--offset={offset}',
            f'--limit={BATCH_SIZE}',
            '--no-input',
            '--delay=0.01'  # Уменьшено
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            cwd=os.getcwd()
        )

        if result.returncode != 0:
            error_msg = f"Ошибка в партии {offset}-{offset + BATCH_SIZE}:\n{result.stderr}"
            logging.error(error_msg)
            return None

        return offset

    except Exception as e:
        logging.error(f"Критическая ошибка: {e}", exc_info=True)
        return None


def main():
    try:
        logging.info("=== Начало импорта ===")
        prepare_database()

        offsets = list(range(0, TOTAL_PRODUCTS, BATCH_SIZE))
        completed = 0

        with tqdm(total=TOTAL_PRODUCTS, desc="Общий прогресс") as pbar:
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {executor.submit(run_import, offset): offset for offset in offsets}

                for future in as_completed(futures):
                    offset = futures[future]
                    result = future.result()
                    if result is not None:
                        completed += min(BATCH_SIZE, TOTAL_PRODUCTS - result)
                    pbar.update(min(BATCH_SIZE, TOTAL_PRODUCTS - offset))

        logging.info(f"Импорт завершен. Успешно: {completed}/{TOTAL_PRODUCTS}")

    except Exception as e:
        logging.critical(f"Фатальная ошибка: {e}", exc_info=True)
        return 1

    return 0

if psutil.virtual_memory().available < 2 * 1024 * 1024 * 1024:  # 2 ГБ
    logging.warning("Мало свободной памяти! Уменьшаем количество потоков.")
    MAX_WORKERS = max(1, MAX_WORKERS - 2)
if __name__ == "__main__":
    exit(main())