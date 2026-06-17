import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()
res = cursor.execute("SELECT 1 FROM servicios_reglas WHERE servicio_id = 2 AND codigo_regla = 'NO_REPETIR_N_CONSECUTIVO'").fetchone()
if not res:
    cursor.execute("""
        INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json)
        VALUES (2, 'NO_REPETIR_N_CONSECUTIVO', '{"modo": "HARD"}')
    """)
    conn.commit()
    print("Regla insertada con éxito.")
else:
    print("La regla ya existía en la base de datos.")
conn.close()
