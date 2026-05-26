import sqlite3
import pandas as pd

def count_real_mixes():
    conn = sqlite3.connect('cronograma_inteligente.db')
    query = """
        SELECT g.fecha, g.turno, g.nombre as persona, p.rol
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id = (SELECT MAX(cronograma_id) FROM guardias)
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("No guardias found.")
        return
        
    df['Fecha'] = pd.to_datetime(df['fecha'])
    df['Semana'] = df['Fecha'].dt.isocalendar().week
    
    grouped = df.groupby(['persona', 'Semana'])
    
    real_mix_count = 0
    compat_mix_count = 0
    
    for (persona, semana), group in grouped:
        turnos = set(group['turno'])
        
        # Determine active base shifts
        has_M = 'M' in turnos
        has_T = 'T' in turnos
        has_TN = 'TN' in turnos
        has_N = 'N' in turnos
        has_MT = 'MT' in turnos
        has_TNN = 'TNN' in turnos
        
        # The solver rules define is_M, is_T, is_TN, is_N:
        # If 'M' is worked -> is_M = 1
        # If 'T' is worked -> is_T = 1
        # If 'TN' is worked -> is_TN = 1
        # If 'N' is worked -> is_N = 1
        # If 'MT' is worked -> is_M + is_T >= 1 (so solver can choose to activate only one of is_M or is_T)
        # If 'TNN' is worked -> is_TN + is_N >= 1 (so solver can choose to activate only one of is_TN or is_N)
        
        # Let's see if there exists a valid assignment of is_M, is_T, is_TN, is_N (all in {0, 1})
        # such that:
        # - if has_M: is_M = 1
        # - if has_T: is_T = 1
        # - if has_TN: is_TN = 1
        # - if has_N: is_N = 1
        # - if has_MT: is_M + is_T >= 1
        # - if has_TNN: is_TN + is_N >= 1
        # And the sum is_M + is_T + is_TN + is_N <= 1 (meaning no mixture)
        
        # If we can satisfy the above with sum <= 1, then the solver could avoid the mixture penalty.
        # Otherwise, it's a real mixture.
        
        # Let's check if it's possible to have no mixture:
        # Can we set sum <= 1?
        # That means at most one of the variables is 1.
        # Let's list the required variables:
        required = set()
        if has_M: required.add('is_M')
        if has_T: required.add('is_T')
        if has_TN: required.add('is_TN')
        if has_N: required.add('is_N')
        
        # We also need to satisfy MT and TNN:
        # - If has_MT: we need either is_M or is_T to be 1.
        # - If has_TNN: we need either is_TN or is_N to be 1.
        
        # Let's find if there is any single variable (among is_M, is_T, is_TN, is_N)
        # that satisfies all conditions:
        possible_single_vars = {'is_M', 'is_T', 'is_TN', 'is_N'}
        
        # Filter by required
        if required:
            possible_single_vars = possible_single_vars.intersection(required)
            
        # Filter by MT
        if has_MT:
            possible_single_vars = possible_single_vars.intersection({'is_M', 'is_T'})
            
        # Filter by TNN
        if has_TNN:
            possible_single_vars = possible_single_vars.intersection({'is_TN', 'is_N'})
            
        if len(possible_single_vars) >= 1:
            # A clean assignment exists with sum <= 1
            pass
        else:
            real_mix_count += 1
            print(f"REAL MIX: {persona} en semana {semana} has turnos: {sorted(list(turnos))}")
            
    print(f"\nResumen:")
    print(f"Total real mixtures: {real_mix_count}")

if __name__ == '__main__':
    count_real_mixes()
