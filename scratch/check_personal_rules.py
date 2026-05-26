import sqlite3
import json

def run_diag():
    conn = sqlite3.connect("cronograma_inteligente.db")
    conn.row_factory = sqlite3.Row
    
    print("=== REGLAS POR PERSONAL PARA SERVICIO 2 ===")
    rows = conn.execute("""
        SELECT pr.personal_nombre, rc.codigo_regla, pr.parametros_json
        FROM personal_reglas pr
        JOIN reglas_catalogo rc ON pr.regla_id = rc.id
        JOIN personal p ON pr.personal_nombre = p.nombre
        WHERE p.servicio_id = 2
    """).fetchall()
    
    for r in rows:
        print(f"Nombre: {r['personal_nombre']} | Regla: {r['codigo_regla']} | Params: {r['parametros_json']}")
        
    conn.close()

if __name__ == '__main__':
    run_diag()
