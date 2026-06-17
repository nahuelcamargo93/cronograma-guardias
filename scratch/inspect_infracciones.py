import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get latest cronograma id
cursor.execute("SELECT max(id) FROM cronogramas")
crono_id = cursor.fetchone()[0]

cursor.execute("""
    SELECT i.codigo_regla, r.descripcion, i.detalle 
    FROM infracciones_debug i
    LEFT JOIN reglas_catalogo r ON i.codigo_regla = r.codigo_regla
    WHERE i.cronograma_id = ?
""", (crono_id,))
infracciones = cursor.fetchall()
print(f"--- INFRACCIONES CRONOGRAMA {crono_id} ({len(infracciones)}) ---")
for idx, (codigo, desc, detalle) in enumerate(infracciones):
    print(f"{idx+1}. Regla: {codigo} | Detalle: {detalle}")
    
conn.close()
