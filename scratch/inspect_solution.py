import sys
sys.path.append(".")
import main
import pandas as pd
import sqlite3

# Let's run optimization for service 3, 2026-06-01 to 2026-06-30
res = main.ejecutar_optimizacion(3, "2026-06-01", "2026-06-30", notas="Test inspect")
print(res)

if res.get("status") == "success":
    cronograma_id = res["cronograma_id"]
    conn = sqlite3.connect("cronograma_inteligente.db")
    df_g = pd.read_sql_query(f"""
        SELECT nombre, fecha, turno, horas
        FROM guardias
        WHERE cronograma_id = {cronograma_id} AND fecha IN ('2026-06-01', '2026-06-02')
        ORDER BY fecha, nombre
    """, conn)
    print("\n--- GENERATED GUARDIAS FOR JUNE 1 & 2 ---")
    print(df_g.to_string())
    conn.close()
