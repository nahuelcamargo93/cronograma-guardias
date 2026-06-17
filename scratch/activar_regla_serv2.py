import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Insertar o actualizar la regla MEZCLA_SEMANAL_DURA para el servicio 2
cursor.execute("""
    INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
    VALUES (2, 'MEZCLA_SEMANAL_DURA', '{}', 1)
    ON CONFLICT(servicio_id, codigo_regla) DO UPDATE SET activo = 1
""")
conn.commit()

print("Verificando regla activa en servicios_reglas para servicio 2:")
cursor.execute("SELECT * FROM servicios_reglas WHERE servicio_id = 2 AND codigo_regla = 'MEZCLA_SEMANAL_DURA'")
print(cursor.fetchone())

conn.close()
