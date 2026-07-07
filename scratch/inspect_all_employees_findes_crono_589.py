import sqlite3
import pandas as pd
from datetime import date, timedelta

conn = sqlite3.connect("cronograma_inteligente.db")

# Cargar profesionales
profesionales = [r[0] for r in conn.cursor().execute("SELECT nombre FROM personal WHERE servicio_id = 2 AND activo = 1 ORDER BY nombre").fetchall()]

# Fines de semana de agosto
findes = [
    ("2026-08-01", "2026-08-02"),
    ("2026-08-08", "2026-08-09"),
    ("2026-08-15", "2026-08-16"),
    ("2026-08-22", "2026-08-23"),
    ("2026-08-29", "2026-08-30")
]

fecha_inicio_dt = date(2026, 8, 1)

print(f"{'Empleado':<30} | {'Tiene FLR en DB':<15} | {'Francos en Finde (S/D)':<25} | {'¿Bloque 4 libres?':<20}")
print("-" * 100)

for nombre in profesionales:
    # Guardias en el crono 589
    df_g = pd.read_sql_query("""
        SELECT fecha FROM guardias 
        WHERE cronograma_id = 589 AND nombre = ?
    """, conn, params=(nombre,))
    guardias_fechas = set(df_g['fecha'].tolist())
    
    # FLR en la DB
    flr_db = conn.cursor().execute("""
        SELECT fecha_inicio, fecha_fin FROM flr_asignados 
        WHERE cronograma_id = 589 AND nombre = ?
    """, (nombre,)).fetchone()
    tiene_flr = f"SI ({flr_db[0]} a {flr_db[1]})" if flr_db else "NO"
    
    # Francos por finde
    finde_stats = []
    for sat, sun in findes:
        sat_libre = "F" if sat not in guardias_fechas else "T"
        sun_libre = "F" if sun not in guardias_fechas else "T"
        finde_stats.append(f"{sat_libre}/{sun_libre}")
    finde_str = " | ".join(finde_stats)
    
    # Bloques de 4 libres
    dias_trabajados = [0] * 31
    for d in range(31):
        fecha_str = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m-%d")
        if fecha_str in guardias_fechas:
            dias_trabajados[d] = 1
            
    bloques_4_libres = []
    for d in range(31 - 3):
        if sum(dias_trabajados[d:d+4]) == 0:
            fi = (fecha_inicio_dt + timedelta(days=d)).strftime("%m-%d")
            ff = (fecha_inicio_dt + timedelta(days=d+3)).strftime("%m-%d")
            bloques_4_libres.append(f"{fi}->{ff}")
            
    bloque_str = ", ".join(bloques_4_libres) if bloques_4_libres else "Ninguno"
    
    # Solo mostrar si no tiene guardias del todo (omitir) o si queremos ver todos
    print(f"{nombre:<30} | {tiene_flr:<15} | {finde_str:<25} | {bloque_str:<20}")

conn.close()
