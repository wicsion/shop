import os
import gc
import sqlite3

# Закроем активное соединение, если оно есть
gc.collect()

# Удаляем файл
try:
    os.remove("db.sqlite3")
    print("Файл db.sqlite3 удалён успешно.")
except Exception as e:
    print(f"Ошибка при удалении: {e}")
