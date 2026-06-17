import sqlite3

def run():
    conn = sqlite3.connect("cronograma_inteligente.db")
    rows = conn.execute("SELECT nombre, rol, categoria FROM personal WHERE servicio_id = 1").fetchall()
    print("--- Personal de Kinesiología en BD ---")
    for r in rows:
        print(r)
    conn.close()

if __name__ == '__main__':
    run()
