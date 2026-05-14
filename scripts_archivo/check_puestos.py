import sqlite3

def check_puestos():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM puestos WHERE servicio_id = 2;")
    print(cursor.fetchall())
    conn.close()

if __name__ == "__main__":
    check_puestos()
