import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    print("=== REGLAS EN CATALOGO ===")
    rows = cursor.execute("SELECT id, codigo_regla, tipo, descripcion FROM reglas_catalogo").fetchall()
    for r in rows:
        print(f"ID: {r[0]} | Codigo: {r[1]} | Tipo: {r[2]} | Desc: {r[3]}")
        
    conn.close()

if __name__ == '__main__':
    main()
