import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    print("=== ASIGNACIONES FIJAS EXISTENTES EN personal_reglas_ajustes ===")
    rows = cursor.execute("""
        SELECT id, personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo
        FROM personal_reglas_ajustes
        WHERE codigo_regla = 'ASIGNACION_FIJA'
        ORDER BY id DESC
        LIMIT 5
    """).fetchall()
    for r in rows:
        print(f"ID: {r[0]} | Nombre: {repr(r[1])} | Regla: {r[2]} | Inicio: {r[3]} | Fin: {r[4]} | Accion: {r[5]} | Params: {r[6]} | Activo: {r[7]}")
        
    conn.close()

if __name__ == '__main__':
    main()
