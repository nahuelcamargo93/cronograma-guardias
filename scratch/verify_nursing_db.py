import sqlite3
import pandas as pd
from datetime import date, timedelta

def verify_nursing_db():
    conn = sqlite3.connect('cronograma_inteligente.db')
    
    # Query assignments for the latest cronograma
    query = """
        SELECT g.fecha, g.turno, g.nombre as persona, p.rol
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id = (SELECT MAX(cronograma_id) FROM guardias)
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("No assignments found for cronograma_id 114.")
        return
        
    df['Fecha'] = pd.to_datetime(df['fecha'])
    df['Semana'] = df['Fecha'].dt.isocalendar().week
    
    # Map shift to shift family (M, T, TN, N)
    def get_families(turno):
        if turno == 'M': return {'M'}
        if turno == 'T': return {'T'}
        if turno == 'TN': return {'TN'}
        if turno == 'N': return {'N'}
        if turno == 'MT': return {'M', 'T'}
        if turno == 'TNN': return {'TN', 'N'}
        return set()

    mix_count = 0
    grouped = df.groupby(['persona', 'Semana'])
    for (persona, semana), group in grouped:
        all_families = set()
        for _, row in group.iterrows():
            fams = get_families(row['turno'])
            all_families.update(fams)
        
        if len(all_families) > 1:
            # Sort by date
            group_sorted = group.sort_values(by='Fecha')
            turnos_sem = list(group_sorted['turno'])
            fechas_sem = [f.strftime('%Y-%m-%d') for f in group_sorted['Fecha']]
            assignments_str = ", ".join([f"{f}: {t}" for f, t in zip(fechas_sem, turnos_sem)])
            print(f"ALERTA: {persona} mezcla familias en la semana {semana}: {assignments_str} (familias: {all_families})")
            mix_count += 1
            
    if mix_count == 0:
        print("EXITO: ¡Nadie mezcló familias de turnos en la misma semana!")
    else:
        print(f"Total de mezclas encontradas: {mix_count}")

if __name__ == '__main__':
    verify_nursing_db()
