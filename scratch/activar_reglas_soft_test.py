import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Activar reglas soft de balance
reglas = ['PESO_BRECHA_MENSUAL', 'PESO_BRECHA_DIARIA_PERSONAL']
for r in reglas:
    cursor.execute("""
        UPDATE servicios_reglas
        SET activo = 1
        WHERE servicio_id = 2 AND codigo_regla = ?
    """, (r,))
conn.commit()

print("Reglas activadas en la BD para el servicio 2:")
cursor.execute("SELECT codigo_regla, activo FROM servicios_reglas WHERE servicio_id = 2 AND codigo_regla IN ('PESO_BRECHA_MENSUAL', 'PESO_BRECHA_DIARIA_PERSONAL')")
for row in cursor.fetchall():
    print(row)

conn.close()
