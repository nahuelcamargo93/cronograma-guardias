import sqlite3
import pandas as pd

def run():
    conn = sqlite3.connect("cronograma_inteligente.db")
    
    query = """
        SELECT g.cronograma_id, c.fecha_inicio, c.fecha_fin, c.estado, c.notas, COUNT(*) as cant_guardias
        FROM guardias g
        JOIN cronogramas c ON g.cronograma_id = c.id
        JOIN personal p ON g.nombre = p.nombre
        WHERE p.servicio_id = 1 AND g.fecha LIKE '2026-06-%'
        GROUP BY g.cronograma_id
    """
    df = pd.read_sql_query(query, conn)
    print("--- Cronogramas de Kinesiología con guardias en Junio 2026 ---")
    print(df.to_string())
    
    conn.close()

if __name__ == '__main__':
    run()
