import sqlite3

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Ver qué reglas estaban activas
    print("Reglas del servicio para el cronograma 359:")
    crono_rules = cursor.execute("""
        SELECT codigo_regla, activo, parametros_json
        FROM servicios_reglas
        WHERE servicio_id = 2
    """).fetchall()
    for r in crono_rules:
        print(f"  {r[0]}: Activo={r[1]}, Params={r[2]}")

    # 2. Ver si hay infracciones de MAX_FRANCOS_SEMANA
    print("\nInfracciones registradas para el cronograma 359:")
    infr = cursor.execute("""
        SELECT codigo_regla, nombre, fecha, etiqueta, descripcion
        FROM infracciones_debug
        WHERE cronograma_id = 359
    """).fetchall()
    for i in infr:
        print(f"  Regla: {i[0]}, Nombre: {i[1]}, Fecha: {i[2]}, Etiqueta: {i[3]}, Desc: {i[4]}")

    conn.close()

if __name__ == '__main__':
    main()
