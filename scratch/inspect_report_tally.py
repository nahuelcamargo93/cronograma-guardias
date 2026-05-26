import sqlite3
import pandas as pd

def inspect_tallies():
    conn = sqlite3.connect('cronograma_inteligente.db')
    # Get the latest cronograma ID
    query = """
        SELECT g.fecha, g.turno, g.nombre as Personal
        FROM guardias g
        WHERE g.cronograma_id = (SELECT MAX(cronograma_id) FROM guardias)
    """
    df_resultados = pd.read_sql_query(query, conn)
    conn.close()
    
    if df_resultados.empty:
        print("No guardias found in database.")
        return

    # Let's count weeks using our new logic
    df_res_week = df_resultados.copy()
    df_res_week['Fecha_dt'] = pd.to_datetime(df_res_week['fecha'])
    df_res_week['Fecha_Lunes'] = df_res_week['Fecha_dt'].apply(lambda x: (x - pd.Timedelta(days=x.weekday())).strftime("%Y-%m-%d"))
    
    nombres = sorted(df_resultados['Personal'].unique())
    print(f"Total personas: {len(nombres)}")
    
    tipos_de_semana = ['M', 'T', 'TN', 'N']
    df_persona = pd.DataFrame(index=nombres, columns=tipos_de_semana).fillna(0)
    
    for nombre in nombres:
        df_persona_week = df_res_week[df_res_week['Personal'] == nombre]
        if not df_persona_week.empty:
            for fecha_lunes, group in df_persona_week.groupby('Fecha_Lunes'):
                turnos_sem = group['turno'].tolist()
                
                count_M = turnos_sem.count('M')
                count_T = turnos_sem.count('T')
                count_TN = turnos_sem.count('TN')
                count_N = turnos_sem.count('N')
                count_MT = turnos_sem.count('MT')
                count_TNN = turnos_sem.count('TNN')
                
                score_M = count_M + count_MT
                score_T = count_T + count_MT
                score_TN = count_TN + count_TNN
                score_N = count_N + count_TNN
                
                scores = {
                    'M': score_M,
                    'T': score_T,
                    'TN': score_TN,
                    'N': score_N
                }
                
                max_cat = None
                max_score = 0
                for cat in ['M', 'T', 'TN', 'N']:
                    if scores[cat] > max_score:
                        max_score = scores[cat]
                        max_cat = cat
                
                if max_cat:
                    df_persona.at[nombre, max_cat] += 1
                    
    df_persona['Total_Semanas'] = df_persona.sum(axis=1)
    print("\nTALLIES DE SEMANAS POR ENFERMERO:")
    print(df_persona.to_string())

if __name__ == '__main__':
    inspect_tallies()
