import sqlite3

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    print("--- REGLAS INDIVIDUALES EN personal_reglas ---")
    rows = cursor.execute("""
        SELECT pr.personal_nombre, pr.codigo_regla, pr.parametros_json, pr.activo, p.horas_mensuales_reglamentarias
        FROM personal_reglas pr
        JOIN personal p ON pr.personal_nombre = p.nombre
        WHERE p.servicio_id = 3
    """).fetchall()
    for row in rows:
        print(f"Nombre: {row[0]} | Regla: {row[1]} | Params: {row[2]} | Activo: {row[3]} | Hs Reg: {row[4]}")
        
    print("\n--- AJUSTES INDIVIDUALES EN personal_reglas_ajustes ---")
    rows_aj = cursor.execute("""
        SELECT pra.personal_nombre, pra.codigo_regla, pra.fecha_inicio, pra.fecha_fin, pra.accion, pra.parametros_json, pra.activo
        FROM personal_reglas_ajustes pra
        JOIN personal p ON pra.personal_nombre = p.nombre
        WHERE p.servicio_id = 3
    """).fetchall()
    for row in rows_aj:
        print(f"Nombre: {row[0]} | Regla: {row[1]} | Rango: {row[2]} a {row[3]} | Accion: {row[4]} | Params: {row[5]} | Activo: {row[6]}")
        
    conn.close()

if __name__ == "__main__":
    main()
