import sqlite3
import os

db_path = 'cronograma_inteligente.db'
print(f"Connecting to database at {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 1. Desactivar MIN_TURNOS para coordinadores
    print("Desactivando MIN_TURNOS para coordinadores...")
    cords = ('Franco, Leandro', 'Moyano, Fernando', 'Toledo, Andrea')
    cursor.execute("""
        UPDATE personal_reglas 
        SET activo = 0 
        WHERE personal_nombre IN (?, ?, ?) 
          AND codigo_regla = 'MIN_TURNOS'
    """, cords)
    print(f"Filas afectadas (coordinadores): {cursor.rowcount}")

    # Opcional: También desactivamos para Garcia, Luciano (Jefe UTI) si corresponde
    cursor.execute("""
        UPDATE personal_reglas 
        SET activo = 0 
        WHERE personal_nombre = 'Garcia, Luciano' 
          AND codigo_regla = 'MIN_TURNOS'
    """)
    print(f"Filas afectadas (jefe Luciano Garcia): {cursor.rowcount}")

    # 2. Activar FINDE_LARGO_REGLAMENTARIO en modo HARD con tipo "vl"
    print("Configurando y activando FINDE_LARGO_REGLAMENTARIO...")
    flr_params = '{"modo": "HARD", "peso_soft": 1000, "por_disponibilidad": {"5": 1, "4": 1, "3": 1, "2": 0, "1": 0}, "flr_permitidos": ["vl"]}'
    cursor.execute("""
        UPDATE servicios_reglas 
        SET activo = 1, 
            parametros_json = ? 
        WHERE servicio_id = 1 AND codigo_regla = 'FINDE_LARGO_REGLAMENTARIO'
    """, (flr_params,))
    print(f"Filas afectadas (FINDE_LARGO_REGLAMENTARIO): {cursor.rowcount}")

    # 3. Activar MANEJO_FINDES en modo SOFT
    print("Configurando y activando MANEJO_FINDES...")
    mf_params = '{"modo": "SOFT", "peso_soft": 10000, "por_disponibilidad": {"5": {"flr": 1, "completos": 2, "medios": 1}, "4": {"flr": 1, "completos": 1, "medios": 1}, "3": {"flr": 1, "completos": 1, "medios": 1}, "2": {"flr": 0, "completos": 1, "medios": 1}, "1": {"flr": 0, "completos": 1, "medios": 0}}, "nivelacion_historica": {"activo": true, "tipo": "ANUAL", "fecha_inicio": "2026-06-22"}}'
    cursor.execute("""
        UPDATE servicios_reglas 
        SET activo = 1,
            parametros_json = ?
        WHERE servicio_id = 1 AND codigo_regla = 'MANEJO_FINDES'
    """, (mf_params,))
    print(f"Filas afectadas (MANEJO_FINDES): {cursor.rowcount}")

    conn.commit()
    print("[OK] Transacción guardada con éxito.")

except Exception as e:
    conn.rollback()
    print(f"[ERROR] Se produjo un error, se hizo rollback: {e}")

finally:
    conn.close()
