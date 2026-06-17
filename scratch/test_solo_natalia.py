import sqlite3
from database.connection import get_connection
import main

def test():
    with get_connection() as conn:
        # Desactivar a nivel de servicio
        conn.execute("UPDATE servicios_reglas SET activo = 0 WHERE servicio_id = 3 AND codigo_regla IN ('MIN_TURNOS_SEMANA', 'MIN_FRANCOS_SEMANA')")
        # Mantener activas para Natalia Polleti
        conn.execute("UPDATE personal_reglas SET activo = 1 WHERE personal_nombre = 'POLETTI NATALIA' AND codigo_regla IN ('MIN_TURNOS_SEMANA', 'MIN_FRANCOS_SEMANA')")
    
    print("\n>>> Probando optimización con reglas activas SOLO para Natalia Polleti...")
    res = main.ejecutar_optimizacion(3, "2026-07-01", "2026-07-31", notas="Test solo Natalia Polleti", modo_debug=False, max_time_in_seconds=60)
    print(f"Resultado: {res}")

if __name__ == '__main__':
    test()
