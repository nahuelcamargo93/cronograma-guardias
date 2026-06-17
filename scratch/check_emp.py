import sqlite3
import json

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

names = ["GOMES STHEFANIA", "ORTIZ LAURA"]

for name in names:
    print(f"\n=== EMPLEADO: {name} ===")
    cursor.execute("SELECT nombre, categoria, rol, servicio_id FROM personal WHERE nombre = ?", (name,))
    print("Personal:", cursor.fetchone())
    
    cursor.execute("SELECT codigo_regla, parametros_json, activo FROM personal_reglas WHERE personal_nombre = ?", (name,))
    print("Reglas:")
    for row in cursor.fetchall():
        print(row)
        
    cursor.execute("SELECT * FROM personal_reglas_ajustes WHERE personal_nombre = ?", (name,))
    print("Ajustes Reglas:")
    for row in cursor.fetchall():
        print(row)
        
conn.close()
