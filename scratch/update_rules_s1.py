import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# 1. Desactivar MANEJO_FINDES para servicio 1
cursor.execute("""
    UPDATE servicios_reglas 
    SET activo = 0 
    WHERE servicio_id = 1 AND codigo_regla = 'MANEJO_FINDES'
""")
print(f"MANEJO_FINDES desactivado. Rows affected: {cursor.rowcount}")

# 2. Configuración para FINDE_LARGO_REGLAMENTARIO
config = {
    "modo": "HARD",
    "peso_soft": 1000,
    "por_disponibilidad": {
        "5": 1,
        "4": 1,
        "3": 1,
        "2": 0,
        "1": 0
    },
    "flr_permitidos": ["vl"]
}
config_str = json.dumps(config)

# Verificar si ya existe FINDE_LARGO_REGLAMENTARIO para servicio 1
row = cursor.execute("""
    SELECT id FROM servicios_reglas 
    WHERE servicio_id = 1 AND codigo_regla = 'FINDE_LARGO_REGLAMENTARIO'
""").fetchone()

if row:
    cursor.execute("""
        UPDATE servicios_reglas 
        SET activo = 1, parametros_json = ? 
        WHERE servicio_id = 1 AND codigo_regla = 'FINDE_LARGO_REGLAMENTARIO'
    """, (config_str,))
    print("FINDE_LARGO_REGLAMENTARIO actualizado.")
else:
    cursor.execute("""
        INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo) 
        VALUES (1, 'FINDE_LARGO_REGLAMENTARIO', ?, 1)
    """, (config_str,))
    print("FINDE_LARGO_REGLAMENTARIO insertado.")

conn.commit()
conn.close()
