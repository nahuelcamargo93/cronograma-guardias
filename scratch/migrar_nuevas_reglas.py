import sqlite3
import json
from database.connection import get_connection
from database.schema import inicializar_db

def migrar():
    print("Inicializando base de datos para asegurar el catálogo...")
    inicializar_db()

    with get_connection() as conn:
        # 1. Asegurar catálogo de reglas para MIN_TURNOS_SEMANA y MIN_FRANCOS_SEMANA
        conn.execute("""
            INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
            VALUES 
                ('MIN_TURNOS_SEMANA', 'HARD', 'Piso mínimo de turnos trabajados por semana calendario'),
                ('MIN_FRANCOS_SEMANA', 'HARD', 'Piso mínimo de francos por semana calendario')
        """)

        # Limpiar cualquier residuo incorrecto en servicio 3
        conn.execute("DELETE FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla IN ('MIN_TURNOS_SEMANA', 'MIN_FRANCOS_SEMANA')")
        conn.execute("DELETE FROM personal_reglas WHERE personal_nombre = 'POLETTI NATALIA' AND codigo_regla IN ('MIN_TURNOS_SEMANA', 'MIN_FRANCOS_SEMANA')")

        # 2. Configurar reglas de servicio para el servicio ID 2 (Enfermería)
        # MIN_TURNOS_SEMANA para Servicio 2
        params_turnos_s = {"min_turnos": 4, "modo": "HARD", "peso_soft": 100000}
        conn.execute("""
            INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
            VALUES (2, 'MIN_TURNOS_SEMANA', ?, 1)
            ON CONFLICT(servicio_id, codigo_regla) DO UPDATE SET
                parametros_json = excluded.parametros_json,
                activo = excluded.activo
        """, (json.dumps(params_turnos_s),))
        print("[OK] MIN_TURNOS_SEMANA configurado para Servicio 2")

        # MIN_FRANCOS_SEMANA para Servicio 2
        params_francos_s = {"min_francos": 2, "modo": "HARD", "peso_soft": 100000}
        conn.execute("""
            INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
            VALUES (2, 'MIN_FRANCOS_SEMANA', ?, 1)
            ON CONFLICT(servicio_id, codigo_regla) DO UPDATE SET
                parametros_json = excluded.parametros_json,
                activo = excluded.activo
        """, (json.dumps(params_francos_s),))
        print("[OK] MIN_FRANCOS_SEMANA configurado para Servicio 2")

        # 3. Configurar reglas personales para Natalia Polleti (con servicio_id = 2)
        nombre_persona = "POLETTI NATALIA"

        # MIN_TURNOS_SEMANA para POLETTI NATALIA en el Servicio 2
        params_turnos_p = {"min_turnos": 2, "modo": "HARD", "peso_soft": 100000}
        conn.execute("""
            INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo, servicio_id)
            VALUES (?, 'MIN_TURNOS_SEMANA', ?, 1, 2)
            ON CONFLICT(personal_nombre, codigo_regla) DO UPDATE SET
                parametros_json = excluded.parametros_json,
                activo = excluded.activo,
                servicio_id = excluded.servicio_id
        """, (nombre_persona, json.dumps(params_turnos_p)))
        print(f"[OK] MIN_TURNOS_SEMANA (min_turnos=2) configurado para {nombre_persona}")

        # MIN_FRANCOS_SEMANA para POLETTI NATALIA en el Servicio 2
        params_francos_p = {"min_francos": 3, "modo": "HARD", "peso_soft": 100000}
        conn.execute("""
            INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo, servicio_id)
            VALUES (?, 'MIN_FRANCOS_SEMANA', ?, 1, 2)
            ON CONFLICT(personal_nombre, codigo_regla) DO UPDATE SET
                parametros_json = excluded.parametros_json,
                activo = excluded.activo,
                servicio_id = excluded.servicio_id
        """, (nombre_persona, json.dumps(params_francos_p)))
        print(f"[OK] MIN_FRANCOS_SEMANA (min_francos=3) configurado para {nombre_persona}")

if __name__ == '__main__':
    migrar()
