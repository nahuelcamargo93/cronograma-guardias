import sqlite3

def find_rule_1():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reglas_catalogo WHERE id = 1;")
    print(cursor.fetchone())
    conn.close()

if __name__ == "__main__":
    find_rule_1()
