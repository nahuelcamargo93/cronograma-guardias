import sqlite3
from database.connection import get_connection
import main

def test_individual():
    # Caso 1: Solo MIN_TURNOS_SEMANA activa
    with get_connection() as conn:
        conn.execute("UPDATE servicios_reglas SET activo = 1 WHERE servicio_id = 2 AND codigo_regla = 'MIN_TURNOS_SEMANA'")
        conn.execute("UPDATE servicios_reglas SET activo = 0 WHERE servicio_id = 2 AND codigo_regla = 'MIN_FRANCOS_SEMANA'")
        conn.execute("UPDATE personal_reglas SET activo = 1 WHERE personal_nombre = 'POLETTI NATALIA' AND codigo_regla = 'MIN_TURNOS_SEMANA'")
        conn.execute("UPDATE personal_reglas SET activo = 0 WHERE personal_nombre = 'POLETTI NATALIA' AND codigo_regla = 'MIN_FRANCOS_SEMANA'")

    print("\n>>> Probando optimización Servicio 2 con SOLO MIN_TURNOS_SEMANA...")
    res1 = main.ejecutar_optimizacion(2, "2026-07-01", "2026-07-31", notas="Test solo min turnos S2", modo_debug=False, max_time_in_seconds=30)
    print(f"Resultado SOLO MIN_TURNOS_SEMANA: {res1}")

    # Caso 2: Solo MIN_FRANCOS_SEMANA activa
    with get_connection() as conn:
        conn.execute("UPDATE servicios_reglas SET activo = 0 WHERE servicio_id = 2 AND codigo_regla = 'MIN_TURNOS_SEMANA'")
        conn.execute("UPDATE servicios_reglas SET activo = 1 WHERE servicio_id = 2 AND codigo_regla = 'MIN_FRANCOS_SEMANA'")
        conn.execute("UPDATE personal_reglas SET activo = 0 WHERE personal_nombre = 'POLETTI NATALIA' AND codigo_regla = 'MIN_TURNOS_SEMANA'")
        conn.execute("UPDATE personal_reglas SET activo = 1 WHERE personal_nombre = 'POLETTI NATALIA' AND codigo_regla = 'MIN_FRANCOS_SEMANA'")

    print("\n>>> Probando optimización Servicio 2 con SOLO MIN_FRANCOS_SEMANA...")
    res2 = main.ejecutar_optimizacion(2, "2026-07-01", "2026-07-31", notas="Test solo min francos S2", modo_debug=False, max_time_in_seconds=30)
    print(f"Resultado SOLO MIN_FRANCOS_SEMANA: {res2}")

    # Reactivar ambas reglas al finalizar
    with get_connection() as conn:
        conn.execute("UPDATE servicios_reglas SET activo = 1 WHERE servicio_id = 2 AND codigo_regla IN ('MIN_TURNOS_SEMANA', 'MIN_FRANCOS_SEMANA')")
        conn.execute("UPDATE personal_reglas SET activo = 1 WHERE personal_nombre = 'POLETTI NATALIA' AND codigo_regla IN ('MIN_TURNOS_SEMANA', 'MIN_FRANCOS_SEMANA')")
    print("Reglas reactivadas.")

if __name__ == '__main__':
    test_individual()
