import sqlite3
import pandas as pd

def check_real_mixes():
    conn = sqlite3.connect('cronograma_inteligente.db')
    query = """
        SELECT g.fecha, g.turno, g.nombre as persona
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id = (SELECT MAX(cronograma_id) FROM guardias)
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("No assignments found.")
        return
        
    df['Fecha'] = pd.to_datetime(df['fecha'])
    df['Semana'] = df['Fecha'].dt.isocalendar().week
    
    # We group by persona and Semana
    grouped = df.groupby(['persona', 'Semana'])
    
    bad_mix_count = 0
    for (persona, semana), group in grouped:
        turnos_sem = set(group['turno'])
        
        # Check for bad mixes:
        # 1. Day family (M, T, MT) mixed with Night family (TN, N, TNN)
        day_shifts = turnos_sem.intersection({'M', 'T', 'MT'})
        night_shifts = turnos_sem.intersection({'TN', 'N', 'TNN'})
        if day_shifts and night_shifts:
            print(f"BAD MIX (Day + Night) for {persona} in week {semana}: {sorted(list(turnos_sem))}")
            bad_mix_count += 1
            
        # 2. Pure M mixed with Pure T in the same week
        if 'M' in turnos_sem and 'T' in turnos_sem:
            print(f"BAD MIX (Pure M + Pure T) for {persona} in week {semana}: {sorted(list(turnos_sem))}")
            bad_mix_count += 1
            
        # 3. Pure TN mixed with Pure N in the same week
        if 'TN' in turnos_sem and 'N' in turnos_sem:
            print(f"BAD MIX (Pure TN + Pure N) for {persona} in week {semana}: {sorted(list(turnos_sem))}")
            bad_mix_count += 1
            
    if bad_mix_count == 0:
        print("EXITO: ¡No se encontró ningún caso de mezcla no permitida en la misma semana!")
    else:
        print(f"Total de mezclas prohibidas: {bad_mix_count}")

if __name__ == '__main__':
    check_real_mixes()
