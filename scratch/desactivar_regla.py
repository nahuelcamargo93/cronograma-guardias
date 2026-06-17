import sqlite3

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    UPDATE servicios_reglas 
    SET activo = 0 
    WHERE servicio_id = 2 AND codigo_regla = 'ESQUEMA_SEMANAL_ENFERMERIA'
""")
conn.commit()
conn.close()
print("Regla ESQUEMA_SEMANAL_ENFERMERIA desactivada.")
