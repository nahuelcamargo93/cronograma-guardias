import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cronograma_inteligente.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT fecha, descripcion FROM feriados ORDER BY fecha")
    rows = cursor.fetchall()
    print(f"Total feriados encontrados: {len(rows)}")
    for r in rows:
        print(f"{r[0]}: {r[1]}")
    conn.close()

if __name__ == "__main__":
    main()
