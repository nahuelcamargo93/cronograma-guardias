import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def diagnostic_monday():
    conn = sqlite3.connect('cronograma_inteligente.db')
    
    fecha_lunes = "2026-06-01"
    personal = pd.read_sql("SELECT nombre FROM personal", conn)['nombre'].tolist()
    licencias = pd.read_sql("SELECT nombre, fecha_inicio, fecha_fin FROM licencias", conn)
    
    disp_lunes = []
    for p in personal:
        lic = licencias[(licencias['nombre'] == p) & (licencias['fecha_inicio'] <= fecha_lunes) & (licencias['fecha_fin'] >= fecha_lunes)]
        if lic.empty:
            disp_lunes.append(p)
            
    print(f"Personas disponibles el Lunes 1/6: {len(disp_lunes)}")
    print(disp_lunes)
    
    print("\n--- EXCLUSIONES DE LOS DISPONIBLES ---")
    for p in disp_lunes:
        excl = pd.read_sql("SELECT parametros_json FROM personal_reglas WHERE personal_nombre = ? AND regla_id = 4", conn, params=(p,))
        if not excl.empty:
            print(f"{p}: {excl.iloc[0]['parametros_json']}")
        else:
            print(f"{p}: Sin exclusiones")
            
    # Needed: Mañana_UTI(2), Tarde_UTI(1), Dia_UTI(1), Mañana_UCO(1), Tarde_UCO(1), Noche(2)
    # Total 8.
    
    conn.close()

if __name__ == "__main__":
    diagnostic_monday()
