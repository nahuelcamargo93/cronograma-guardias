import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== PUESTOS HABILITADOS Y PRIMARIOS EN SERVICIO 3 ===")
cursor.execute("""
    SELECT pp.personal_nombre, p.nombre, COALESCE(pp.es_primario, 1)
    FROM personal_puestos pp
    JOIN puestos p ON pp.puesto_id = p.id
    WHERE p.servicio_id = 3 AND (pp.personal_nombre = 'Aguilera Graciela' OR pp.personal_nombre LIKE '%Garcia Rodriguez%')
""")
for r in cursor.fetchall():
    print(r)

# Ver todos los puestos de la base de datos para el servicio 3
print("\n=== TODOS LOS PUESTOS DEL SERVICIO 3 ===")
cursor.execute("SELECT id, nombre FROM puestos WHERE servicio_id = 3")
for r in cursor.fetchall():
    print(r)

conn.close()
