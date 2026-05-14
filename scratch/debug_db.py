import sqlite3
import json

def debug_config():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    servicio_id = 1
    fecha_inicio = "2026-05-25"
    fecha_fin = "2026-07-05"

    # 1. Ver turnos base
    print("--- TURNOS CONFIG (Base) ---")
    rows = cursor.execute("SELECT id, nombre, vacantes_semana, vacantes_finde FROM turnos_config WHERE servicio_id = ?", (servicio_id,)).fetchall()
    for r in rows:
        print(f"ID: {r[0]} | {r[1]:<15} | Sem: {r[2]} | Fin: {r[3]}")

    # 2. Ver ajustes
    print("\n--- TURNOS AJUSTES ---")
    rows_ajustes = cursor.execute("""
        SELECT ta.fecha_inicio, ta.fecha_fin, tc.nombre, ta.vacantes
        FROM turnos_ajustes ta
        JOIN turnos_config tc ON ta.turno_config_id = tc.id
        WHERE tc.servicio_id = ?
    """, (servicio_id,)).fetchall()
    for r in rows_ajustes:
        print(f"{r[0]} a {r[1]} | {r[2]:<15} | Vacantes: {r[3]}")

    conn.close()

if __name__ == "__main__":
    debug_config()
