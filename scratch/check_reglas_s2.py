import sys
sys.path.insert(0, r'c:\Users\asus\Desktop\Ryoko\cronograma_inteligente')
import json
from database.connection import get_connection

with get_connection() as conn:
    # Ver schema de reglas_catalogo
    row = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='reglas_catalogo'").fetchone()
    print("Schema reglas_catalogo:", row[0])
    
    # Ver columnas disponibles
    sample = conn.execute("SELECT * FROM reglas_catalogo LIMIT 2").fetchall()
    if sample:
        cols = [d[0] for d in conn.execute("SELECT * FROM reglas_catalogo LIMIT 1").description]
        print("Columnas:", cols)
        print("Ejemplo:", sample[:2])
