import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
rows = conn.execute("SELECT etiqueta FROM infracciones_debug WHERE cronograma_id=334 AND codigo_regla='MAX_FRANCOS_SEMANA'").fetchall()
for r in rows:
    print(r[0])
print()
# También ver esquema_semanal
rows2 = conn.execute("SELECT etiqueta FROM infracciones_debug WHERE cronograma_id=334 AND codigo_regla='ESQUEMA_SEMANAL_ENFERMERIA'").fetchall()
print("ESQUEMA_SEMANAL_ENFERMERIA infracciones:")
for r in rows2:
    print(f"  {r[0]}")
conn.close()
