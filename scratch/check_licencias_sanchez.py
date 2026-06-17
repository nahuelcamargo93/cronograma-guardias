import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- Licencias de Sánchez Reinoso ---")
cursor.execute("SELECT tipo, fecha_inicio, fecha_fin, activa FROM licencias WHERE nombre LIKE '%Sánchez Reinoso%'")
for r in cursor.fetchall():
    print(r)

print("\n--- Credito horario licencia regla para servicio 3 ---")
cursor.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla = 'CREDITO_HORARIO_LICENCIA'")
for r in cursor.fetchall():
    print(r)

conn.close()
