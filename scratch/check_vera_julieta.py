import sqlite3
import json

DB_PATH = "cronograma_inteligente.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=== PERSONAL DETAILS: VELIZ LIONEL ===")
    cursor.execute("SELECT * FROM personal WHERE nombre = 'VELIZ LIONEL'")
    print(cursor.fetchone())

    print("\n=== LICENCIAS DE VELIZ LIONEL ===")
    cursor.execute("SELECT * FROM licencias WHERE nombre = 'VELIZ LIONEL'")
    for r in cursor.fetchall():
        print(r)

    print("\n=== REGLAS INDIVIDUALES DE VELIZ LIONEL ===")
    cursor.execute("SELECT * FROM personal_reglas WHERE personal_nombre = 'VELIZ LIONEL'")
    for r in cursor.fetchall():
        print(r)

    conn.close()

if __name__ == '__main__':
    main()
