import sqlite3

def find_people():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    names = ['Olguin', 'Nievas', 'Boria', 'Fernandez']
    for name in names:
        cursor.execute("SELECT nombre FROM personal WHERE nombre LIKE ?;", ('%' + name + '%',))
        results = cursor.fetchall()
        print(f"Search for '{name}': {results}")
    conn.close()

if __name__ == "__main__":
    find_people()
