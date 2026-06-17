import sqlite3
from datetime import date

db_path = "cronograma_inteligente.db"

def inspect():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Cronogramas guardados
    print("--- Cronogramas ---")
    cursor.execute("SELECT id, fecha_inicio, fecha_fin, estado, notas FROM cronogramas ORDER BY fecha_inicio DESC")
    cronogramas = cursor.fetchall()
    for row in cronogramas:
        print(f"ID: {row[0]}, Inicio: {row[1]}, Fin: {row[2]}, Estado: {row[3]}, Notas: {row[4]}")

    # 2. Buscar último cronograma aprobado anterior a 2026-07-01 para servicio 2
    print("\n--- Último cronograma aprobado antes de 2026-07-01 para servicio 2 ---")
    cursor.execute("""
        SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin FROM cronogramas c
        JOIN guardias g ON c.id = g.cronograma_id
        JOIN personal p ON g.nombre = p.nombre
        WHERE c.estado = 'aprobado' AND c.fecha_inicio < '2026-07-01' AND p.servicio_id = 2
        ORDER BY c.fecha_inicio DESC
        LIMIT 1
    """)
    row_cr = cursor.fetchone()
    if row_cr:
        print(f"Último cronograma: ID={row_cr[0]}, Inicio={row_cr[1]}, Fin={row_cr[2]}")
        # Guardias en el rango 2026-06-29 y 2026-06-30
        print("\n--- Guardias del 2026-06-29 y 2026-06-30 en ese cronograma ---")
        cursor.execute("""
            SELECT g.nombre, g.fecha, g.turno, g.horas
            FROM guardias g
            WHERE g.cronograma_id = ? AND g.fecha IN ('2026-06-29', '2026-06-30')
            ORDER BY g.nombre, g.fecha
        """, [row_cr[0]])
        guardias = cursor.fetchall()
        for g in guardias:
            print(f"Nombre: {g[0]}, Fecha: {g[1]}, Turno: {g[2]}, Horas: {g[3]}")
    else:
        print("No se encontró cronograma previo aprobado para el servicio 2.")

    # 3. Guardias de ABELENDA GRISELL en cualquier cronograma para junio
    print("\n--- Todas las guardias de ABELENDA GRISELL en junio 2026 ---")
    cursor.execute("""
        SELECT g.cronograma_id, g.fecha, g.turno, g.horas, c.estado
        FROM guardias g
        JOIN cronogramas c ON g.cronograma_id = c.id
        WHERE g.nombre LIKE '%ABELENDA%' AND g.fecha LIKE '2026-06-%'
        ORDER BY g.fecha
    """)
    for row in cursor.fetchall():
         print(f"CrID: {row[0]} ({row[4]}), Fecha: {row[1]}, Turno: {row[2]}, Horas: {row[3]}")

    conn.close()

if __name__ == "__main__":
    inspect()
