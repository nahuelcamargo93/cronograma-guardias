import sqlite3

def list_catalog():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reglas_catalogo LIMIT 20;")
    for row in cursor.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    list_catalog()
