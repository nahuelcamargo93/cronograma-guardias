import sqlite3
import json

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("--- REGLAS EN SERVICIOS_REGLAS PARA SERVICIO 3 ---")
    rows = cur.execute("""
        SELECT codigo_regla, parametros_json, activo
        FROM servicios_reglas
        WHERE servicio_id = 3
    """).fetchall()
    for row in rows:
        print(f"Regla: {row['codigo_regla']} | Activo: {row['activo']} | Params: {row['parametros_json']}")

    print("\n--- REGLAS INDIVIDUALES EN PERSONAL_REGLAS (SERVICIO 3) ---")
    rows = cur.execute("""
        SELECT pr.personal_nombre, pr.codigo_regla, pr.parametros_json, pr.activo
        FROM personal_reglas pr
        JOIN personal p ON pr.personal_nombre = p.nombre
        WHERE p.servicio_id = 3
    """).fetchall()
    for row in rows:
        print(f"Personal: {row['personal_nombre']} | Regla: {row['codigo_regla']} | Activo: {row['activo']} | Params: {row['parametros_json']}")

    print("\n--- DETALLES DE PERSONAL DE SERVICIO 3 ---")
    rows = cur.execute("""
        SELECT nombre, rol, categoria, activo
        FROM personal
        WHERE servicio_id = 3
    """).fetchall()
    for row in rows:
        print(f"Nombre: {row['nombre']} | Rol: {row['rol']} | Categoria: {row['categoria']} | Activo: {row['activo']}")

    conn.close()

if __name__ == '__main__':
    main()
