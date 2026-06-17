import sqlite3
import pandas as pd

def run():
    conn = sqlite3.connect("cronograma_inteligente.db")
    query = """
        SELECT g.fecha, c.id as cronograma_id, c.estado, COUNT(*) as cant_guardias
        FROM guardias g
        JOIN cronogramas c ON g.cronograma_id = c.id
        JOIN personal p ON g.nombre = p.nombre
        WHERE p.servicio_id = 1 AND g.fecha BETWEEN '2026-05-25' AND '2026-05-31'
        GROUP BY g.fecha, c.id
    """
    df = pd.read_sql_query(query, conn)
    print("--- Guardias de Kinesiología del 25 al 31 de Mayo en la BD ---")
    print(df)
    conn.close()

if __name__ == '__main__':
    run()
