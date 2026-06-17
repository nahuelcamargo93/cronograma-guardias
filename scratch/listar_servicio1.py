import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cronograma_inteligente.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM personal WHERE servicio_id = 1 ORDER BY nombre")
    rows = cursor.fetchall()
    print("Personal del Servicio 1:")
    for r in rows:
        print(f"'{r[0]}'")
    conn.close()

if __name__ == "__main__":
    main()
