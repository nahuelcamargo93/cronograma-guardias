import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    print("--- LICENCIAS EN JUNIO 2026 ---")
    rows = conn.execute("""
        SELECT nombre, tipo, fecha_inicio, fecha_fin 
        FROM licencias
        WHERE fecha_inicio <= '2026-06-30' AND fecha_fin >= '2026-06-01'
        ORDER BY nombre, fecha_inicio
    """).fetchall()
    for r in rows:
        print(f"Name: {r[0]}, Type: {r[1]}, Range: {r[2]} to {r[3]}")
        
    print("\n--- ACUMULADOS PREVIOS A JUNIO 2026 ---")
    # Let's inspect the historical values of findes_semanas_previos and findes_habiles_previos
    # which are loaded from historical records in the database
    # In `database/data_loader.py` or `queries.py` let's see how they are calculated
    from database.queries import cargar_historial
    df_p = pd_personal = conn.execute("SELECT nombre FROM personal WHERE servicio_id = 4").fetchall()
    import pandas as pd
    df_p_pd = pd.DataFrame([r[0] for r in df_p], columns=['Nombre'])
    hist = cargar_historial(df_p_pd, "2026-06-01")
    
    # Filter for group 12-18 (since Mocdese and Suñer are in that group)
    group_12_18 = [
        "BARROSO Alan", "SUÑER Mara Tatiana", "FLORES Jose Nicolas", 
        "GUERRERO Cesar", "MOCDESE Marcelo Leonel", "VERGARA Nazareno", "VILLEGAS Gaston"
    ]
    print("\n[Group 12-18 History prior to June 2026]")
    for name in group_12_18:
        if name in hist:
            print(f"  {name}: {hist[name]}")

if __name__ == "__main__":
    inspect()
