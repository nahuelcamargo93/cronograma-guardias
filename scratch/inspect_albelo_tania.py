import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- DATOS DE ALBELO TANIA EN LA BD ---")
cursor.execute("SELECT nombre, categoria, rol, servicio_id, regimen_trabajo, activo FROM personal WHERE nombre = 'ALBELO TANIA'")
print("Personal:", cursor.fetchone())

# Puestos habilitados
cursor.execute("SELECT puesto_id FROM personal_puestos WHERE personal_nombre = 'ALBELO TANIA'")
print("Puestos Habilitados:", cursor.fetchall())

# Licencias
cursor.execute("SELECT tipo, fecha_inicio, fecha_fin FROM licencias WHERE nombre = 'ALBELO TANIA'")
print("Licencias:", cursor.fetchall())

# Guardias asignadas en el cronograma 260
cursor.execute("SELECT fecha, turno, horas FROM guardias WHERE cronograma_id = 260 AND nombre = 'ALBELO TANIA'")
print("Guardias asignadas en crono 260:")
for r in cursor.fetchall():
    print(r)

conn.close()
