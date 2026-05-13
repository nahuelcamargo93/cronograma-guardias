import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Update Mañana_UTI (ID 5) vacantes to 3 for Semana 2
cursor.execute("UPDATE turnos_ajustes SET vacantes = 3 WHERE fecha_inicio = '2026-06-08' AND turno_config_id = 5")
print(f"Updated Mañana_UTI vacantes to 3 for Semana 2. Rows affected: {cursor.rowcount}")

conn.commit()
conn.close()
