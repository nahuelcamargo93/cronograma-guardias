import sqlite3

def check_all_staff():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    names = ['OLGUIN', 'NIEVAS', 'BORIA', 'FERNANDEZ']
    for name in names:
        cursor.execute("SELECT nombre, servicio_id FROM personal WHERE nombre LIKE ?;", ('%' + name + '%',))
        print(f"Results for {name}: {cursor.fetchall()}")
    conn.close()

if __name__ == "__main__":
    check_all_staff()
