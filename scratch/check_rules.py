import sqlite3
import json

def run_diag():
    conn = sqlite3.connect("cronograma_inteligente.db")
    conn.row_factory = sqlite3.Row
    
    print("=== REGLAS ACTIVAS PARA SERVICIO 2 ===")
    rows = conn.execute("""
        SELECT rc.codigo_regla, sr.parametros_json, rc.tipo, rc.descripcion
        FROM servicios_reglas sr
        JOIN reglas_catalogo rc ON sr.regla_id = rc.id
        WHERE sr.servicio_id = 2
    """).fetchall()
    
    for r in rows:
        print(f"Código: {r['codigo_regla']} | Tipo: {r['tipo']} | Params: {r['parametros_json']}")
        
    conn.close()

if __name__ == '__main__':
    run_diag()
