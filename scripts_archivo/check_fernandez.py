import sqlite3

def check_fernandez():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, servicio_id FROM personal WHERE nombre LIKE '%FERNANDEZ%';")
    for row in cursor.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    check_fernandez()
