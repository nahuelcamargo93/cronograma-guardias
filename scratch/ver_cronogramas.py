import sqlite3
import pandas as pd

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    query = """
        SELECT id, fecha_inicio, fecha_fin, estado, notas
        FROM cronogramas
        ORDER BY fecha_inicio DESC
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_string())
    conn.close()

if __name__ == "__main__":
    main()
