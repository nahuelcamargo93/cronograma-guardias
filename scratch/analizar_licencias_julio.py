import sqlite3

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    print("--- LICENCIAS EN JULIO 2026 ---")
    rows = cursor.execute("""
        SELECT l.nombre, l.tipo, l.fecha_inicio, l.fecha_fin, l.metadata
        FROM licencias l
        JOIN personal p ON l.nombre = p.nombre
        WHERE p.servicio_id = 3 AND l.fecha_inicio <= '2026-07-31' AND l.fecha_fin >= '2026-07-01'
    """).fetchall()
    for row in rows:
        print(f"Nombre: {row[0]} | Tipo: {row[1]} | Rango: {row[2]} a {row[3]} | Motivo: {row[4]}")
        
    print("\n--- FRANCOS FORZADOS EN JULIO 2026 ---")
    rows_ff = cursor.execute("""
        SELECT pra.personal_nombre, pra.codigo_regla, pra.fecha_inicio, pra.fecha_fin, pra.activo
        FROM personal_reglas_ajustes pra
        JOIN personal p ON pra.personal_nombre = p.nombre
        WHERE p.servicio_id = 3 AND pra.codigo_regla = 'FRANCO_FORZADO' AND pra.fecha_inicio <= '2026-07-31' AND pra.fecha_fin >= '2026-07-01' AND pra.activo = 1
    """).fetchall()
    for row in rows_ff:
        print(f"Nombre: {row[0]} | Regla: {row[1]} | Rango: {row[2]} a {row[3]} | Activo: {row[4]}")
        
    conn.close()

if __name__ == "__main__":
    main()
