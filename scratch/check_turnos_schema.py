import sqlite3

def check_turnos_schema():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(turnos_config);")
    for row in cursor.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    check_turnos_schema()
