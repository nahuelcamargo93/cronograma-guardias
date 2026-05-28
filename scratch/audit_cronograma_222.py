import sqlite3
import pandas as pd
import datetime
from datetime import date, timedelta
import db as database

def audit():
    print("=== AUDITANDO CRONOGRAMA 222 ===")
    
    # 1. Load guardias from DB for cronograma 222
    with database.get_connection() as conn:
        df_guardias = pd.read_sql("SELECT * FROM guardias WHERE cronograma_id = 222", conn)
        
    if df_guardias.empty:
        print("Error: No guardias found for Cronograma 222.")
        return
        
    print(f"Total guardias: {len(df_guardias)}")

    # 2. Group by professional to see worked weekends and Fridays
    # Let's define the weekends
    fecha_inicio_dt = date.fromisoformat("2026-06-01")
    
    # Findes definition
    findes = {}
    for d in range(30):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        # Check if weekend or holiday
        # (Feriados in June: 2026-06-15, 2026-06-20)
        es_feriado = fecha_d.isoformat() in ["2026-06-15", "2026-06-20"]
        es_finde = fecha_d.weekday() >= 5 or es_feriado
        if es_finde:
            # group by week (Monday of that week)
            lunes = (fecha_d - timedelta(days=fecha_d.weekday())).isoformat()
            findes.setdefault(lunes, []).append(fecha_d.isoformat())
            
    # For each professional, count how many weekends they worked
    res_audit = []
    with database.get_connection() as conn:
        personal = [r[0] for r in conn.execute("SELECT nombre FROM personal WHERE servicio_id = 3 AND COALESCE(activo, 1) = 1").fetchall()]
        
    for p in personal:
        p_guardias = df_guardias[df_guardias['nombre'] == p]
        fechas_trabajadas = set(p_guardias['fecha'].tolist())
        
        # worked weekends
        findes_trabajados = 0
        for lunes, dias in findes.items():
            if any(d in fechas_trabajadas for d in dias):
                findes_trabajados += 1
                
        # worked Fridays
        viernes_trabajados = sum(1 for f in fechas_trabajadas if date.fromisoformat(f).weekday() == 4)
        
        # Load rule parameters
        # For Service 3, EXACTO_FINDE_Y_DIA rule parameters
        # target findes = 2, target Fridays = 1 (since k=4, k_dia=4 for most without licencias)
        res_audit.append({
            'nombre': p,
            'findes_trabajados': findes_trabajados,
            'viernes_trabajados': viernes_trabajados
        })
        
    df_audit = pd.DataFrame(res_audit)
    print(df_audit)

if __name__ == '__main__':
    audit()
