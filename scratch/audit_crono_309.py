import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

crono_id = 309

print(f"=== AUDITORÍA FINES DE SEMANA - CRONOGRAMA ID {crono_id} ===")

df_guardias = pd.read_sql_query("""
    SELECT nombre, fecha, turno, horas
    FROM guardias
    WHERE cronograma_id = ? AND es_finde = 1
    ORDER BY nombre, fecha
""", conn, params=(crono_id,))

df_personal = pd.read_sql_query("""
    SELECT nombre
    FROM personal
    WHERE servicio_id = 1 AND activo = 1
""", conn)

df_guardias['fecha_dt'] = pd.to_datetime(df_guardias['fecha'])
df_guardias['semana_lunes'] = df_guardias['fecha_dt'] - pd.to_timedelta(df_guardias['fecha_dt'].dt.weekday, unit='D')
df_guardias['semana_lunes'] = df_guardias['semana_lunes'].dt.strftime('%Y-%m-%d')

print(f"{'Personal':<20} | {'Días Trab.':<10} | {'Completos':<10} | {'Medios':<10} | {'Total Findes':<12}")
print("-" * 65)

resumen = []
for p in df_personal['nombre']:
    p_guardias = df_guardias[df_guardias['nombre'] == p]
    semanas_trabajadas = p_guardias['semana_lunes'].unique()
    
    completos = 0
    medios = 0
    dias_totales = len(p_guardias)
    
    for sem in semanas_trabajadas:
        sem_g = p_guardias[p_guardias['semana_lunes'] == sem]
        real_sab_dom = [d for d in sem_g['fecha_dt'].dt.weekday if d in (5, 6)]
        if len(set(real_sab_dom)) == 2:
            completos += 1
        elif len(set(real_sab_dom)) == 1:
            medios += 1
            
    print(f"{p:<20} | {dias_totales:<10} | {completos:<10} | {medios:<10} | {completos + medios:<12}")
    
    resumen.append({
        'Personal': p,
        'Dias_Finde_Trabajados': dias_totales,
        'Findes_Completos': completos,
        'Findes_Medios': medios,
        'Findes_Trabajados_Total': completos + medios
    })

conn.close()
