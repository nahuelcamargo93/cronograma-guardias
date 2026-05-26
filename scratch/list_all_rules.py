import sqlite3

def run():
    conn = sqlite3.connect("cronograma_inteligente.db")
    conn.row_factory = sqlite3.Row
    print("=== TODOS LOS REGLAS DEL CATÁLOGO ===")
    rows = conn.execute("SELECT id, codigo_regla, tipo, descripcion FROM reglas_catalogo").fetchall()
    for r in rows:
        print(f"ID: {r['id']} | Código: {r['codigo_regla']} | Tipo: {r['tipo']} | Desc: {r['descripcion']}")
    conn.close()

if __name__ == '__main__':
    run()
