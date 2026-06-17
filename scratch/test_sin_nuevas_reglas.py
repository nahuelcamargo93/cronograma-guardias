import sqlite3
from database.connection import get_connection
import main

def test():
    with get_connection() as conn:
        conn.execute("UPDATE servicios_reglas SET activo = 0 WHERE servicio_id = 3 AND codigo_regla IN ('MIN_TURNOS_SEMANA', 'MIN_FRANCOS_SEMANA')")
        conn.execute("UPDATE personal_reglas SET activo = 0 WHERE servicio_id = 3 AND codigo_regla IN ('MIN_TURNOS_SEMANA', 'MIN_FRANCOS_SEMANA')")
    
    print("\n>>> Probando optimización SIN las nuevas reglas...")
    # Corremos la optimización normal (debería dar INFEASIBLE si ya era inviable de por sí)
    res = main.ejecutar_optimizacion(3, "2026-07-01", "2026-07-31", notas="Test sin nuevas reglas", modo_debug=False, max_time_in_seconds=60)
    print(f"Resultado sin nuevas reglas: {res}")

    # Reactivamos las reglas
    with get_connection() as conn:
        conn.execute("UPDATE servicios_reglas SET activo = 1 WHERE servicio_id = 3 AND codigo_regla IN ('MIN_TURNOS_SEMANA', 'MIN_FRANCOS_SEMANA')")
        conn.execute("UPDATE personal_reglas SET activo = 1 WHERE servicio_id = 3 AND codigo_regla IN ('MIN_TURNOS_SEMANA', 'MIN_FRANCOS_SEMANA')")
    print("Reglas reactivadas.")

if __name__ == '__main__':
    test()
