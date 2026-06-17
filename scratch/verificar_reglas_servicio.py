import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cronograma_inteligente.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sr.id, sr.codigo_regla, sr.parametros_json, sr.activo, rc.descripcion
        FROM servicios_reglas sr
        JOIN reglas_catalogo rc ON sr.codigo_regla = rc.codigo_regla
        WHERE sr.servicio_id = 1
    """)
    rows = cursor.fetchall()
    print("Reglas del Servicio 1 en la base de datos:")
    for r in rows:
        print(f"ID: {r[0]} | Regla: {r[1]} | Activo: {r[3]} | Desc: {r[4]} | Params: {r[2]}")
    conn.close()

if __name__ == "__main__":
    main()
