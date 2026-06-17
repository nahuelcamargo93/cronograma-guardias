import sqlite3
import json

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Leer la configuración actual de MANEJO_FINDES para el servicio 2
row = cursor.execute("""
    SELECT parametros_json 
    FROM servicios_reglas 
    WHERE servicio_id = 2 AND codigo_regla = 'MANEJO_FINDES'
""").fetchone()

if row and row[0]:
    params = json.loads(row[0])
    
    # 2. Agregar 'flr_permitidos': ['sm']
    params['flr_permitidos'] = ["sm"]
    
    # 3. Guardar de nuevo
    cursor.execute("""
        UPDATE servicios_reglas
        SET parametros_json = ?
        WHERE servicio_id = 2 AND codigo_regla = 'MANEJO_FINDES'
    """, (json.dumps(params),))
    
    print("Regra MANEJO_FINDES modificada con flr_permitidos: ['sm'].")
else:
    print("Error: No se encontró la regla MANEJO_FINDES para el servicio 2.")

conn.commit()
conn.close()
