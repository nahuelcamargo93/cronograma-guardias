import sqlite3
import json

def check_fixed():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    query = """
    SELECT pr.personal_nombre, pr.parametros_json
    FROM personal_reglas pr
    JOIN reglas_catalogo rc ON pr.regla_id = rc.id
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 2 AND rc.codigo_regla = 'ASIGNACION_FIJA'
    """
    
    rows = cursor.execute(query).fetchall()
    print(f"Encontradas {len(rows)} asignaciones fijas para Enfermería.")
    for nombre, params in rows:
        print(f"{nombre}: {params}")
    
    conn.close()

if __name__ == "__main__":
    check_fixed()
