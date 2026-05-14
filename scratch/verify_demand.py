import sqlite3

def verify_demand():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM demanda_config WHERE puesto_id = 9;")
    rows = cursor.fetchall()
    print(f"Total rows: {len(rows)}")
    for row in rows:
        print(row)
    conn.close()

if __name__ == "__main__":
    verify_demand()
