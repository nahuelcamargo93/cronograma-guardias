import sqlite3
import json

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Reglas fijas de POLETTI NATALIA (personal_reglas):")
    rows = cursor.execute("""
        SELECT codigo_regla, parametros_json, activo
        FROM personal_reglas
        WHERE personal_nombre = 'POLETTI NATALIA'
    """).fetchall()
    for r in rows:
        print(f"  {r[0]}: {r[1]} (Activo: {r[2]})")

    print("\nAjustes temporales de POLETTI NATALIA (personal_reglas_ajustes):")
    rows_aj = cursor.execute("""
        SELECT codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo
        FROM personal_reglas_ajustes
        WHERE personal_nombre = 'POLETTI NATALIA'
    """).fetchall()
    for r in rows_aj:
        print(f"  {r[0]}: {r[1]} al {r[2]}, Accion: {r[3]}, Params: {r[4]} (Activo: {r[5]})")

    conn.close()

if __name__ == '__main__':
    main()
