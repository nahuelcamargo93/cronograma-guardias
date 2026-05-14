import sqlite3

def check_ajustes_schema():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(personal_reglas_ajustes);")
    for row in cursor.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    check_ajustes_schema()
