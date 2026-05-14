import sqlite3

def find_flr():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reglas_catalogo WHERE codigo_regla = 'FINDE_LARGO_REGLAMENTARIO';")
    print(cursor.fetchone())
    conn.close()

if __name__ == "__main__":
    find_flr()
