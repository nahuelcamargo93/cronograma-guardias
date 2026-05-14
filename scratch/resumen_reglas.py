import sqlite3
import json

def summarize_rules():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    query = """
    SELECT rc.codigo_regla, rc.tipo, rc.descripcion, sr.parametros_json
    FROM servicios_reglas sr
    JOIN reglas_catalogo rc ON sr.regla_id = rc.id
    WHERE sr.servicio_id = 2
    """
    
    rows = cursor.execute(query).fetchall()
    
    print("RESUMEN DE REGLAS - SERVICIO ENFERMERÍA (ID: 2)")
    print("-" * 60)
    for codigo, tipo, desc, params in rows:
        print(f"[{tipo}] {codigo}")
        print(f"   Desc: {desc}")
        print(f"   Config: {params}")
        print("-" * 30)
    
    conn.close()

if __name__ == "__main__":
    summarize_rules()
