import sqlite3
import pandas as pd

def run():
    conn = sqlite3.connect("cronograma_inteligente.db")
    
    query = """
        SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin, c.estado, c.notas
        FROM cronogramas c
        JOIN guardias g ON c.id = g.cronograma_id
        JOIN personal p ON g.nombre = p.nombre
        WHERE p.servicio_id = 1
        ORDER BY c.fecha_inicio
    """
    df = pd.read_sql_query(query, conn)
    print("--- Cronogramas de Kinesiología en BD ---")
    print(df.to_string())
    
    # Veamos si hay algún cronograma que empiece en Junio
    print("\n--- Guardias de Kinesiología en Junio 2026 en la BD ---")
    q_junio = """
        SELECT g.fecha, COUNT(*) as cant
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE p.servicio_id = 1 AND g.fecha LIKE '2026-06-%'
        GROUP BY g.fecha
        ORDER BY g.fecha
    """
    df_j = pd.read_sql_query(q_junio, conn)
    print(df_j)
    
    conn.close()

if __name__ == '__main__':
    run()
