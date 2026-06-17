import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

profesionales = ['Lic. Camargo N.', 'Lic. Giaccoppo', 'Lic. Coniglio']
puesto_especial = 4
servicio_id = 1

print("Insertando puesto Especial (4) para los profesionales...")
for prof in profesionales:
    try:
        # Verificar si ya existe para no duplicar
        cursor.execute("""
            SELECT 1 FROM personal_puestos 
            WHERE personal_nombre = ? AND puesto_id = ?
        """, (prof, puesto_especial))
        
        if cursor.fetchone():
            print(f"El puesto Especial ya está asignado a {prof}.")
        else:
            cursor.execute("""
                INSERT INTO personal_puestos (personal_nombre, puesto_id, servicio_id) 
                VALUES (?, ?, ?)
            """, (prof, puesto_especial, servicio_id))
            print(f"Puesto Especial asignado correctamente a {prof}.")
    except Exception as e:
        print(f"Error al insertar para {prof}: {e}")

conn.commit()
conn.close()
print("Conexión cerrada. Base de datos liberada.")
