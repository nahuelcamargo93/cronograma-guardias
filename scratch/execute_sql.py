import sqlite3

try:
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    with open("scratch/aplicar_cambios.sql", "r", encoding="utf-8") as f:
        sql_content = f.read()
    
    # Ejecutar las sentencias
    cursor.executescript(sql_content)
    conn.commit()
    print("SUCCESS: Cambios aplicados correctamente en la base de datos.")
except Exception as e:
    print(f"ERROR: No se pudieron aplicar los cambios. Detalle: {e}")
finally:
    if conn:
        conn.close()
