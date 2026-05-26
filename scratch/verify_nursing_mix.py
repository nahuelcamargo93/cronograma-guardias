import pandas as pd

def check_nursing_mix():
    df = pd.read_excel('Cronograma_Enfermeria_UTI.xlsx', sheet_name='Cronograma')
    fechas = [c for c in df.columns if c != 'Turno']
    
    results = []
    for _, row in df.iterrows():
        turno = str(row['Turno']).strip()
        for fecha in fechas:
            persona = row[fecha]
            if pd.notna(persona) and persona != "":
                results.append({'Fecha': fecha, 'Turno': turno, 'Persona': persona})
                
    df_long = pd.DataFrame(results)
    df_long['Fecha'] = pd.to_datetime(df_long['Fecha'])
    df_long['Semana'] = df_long['Fecha'].dt.isocalendar().week
    
    # Map shift to shift family (M, T, TN, N)
    # MT -> covers M and T
    # TNN -> covers TN and N
    def get_families(turno):
        if turno == 'M': return {'M'}
        if turno == 'T': return {'T'}
        if turno == 'TN': return {'TN'}
        if turno == 'N': return {'N'}
        if turno == 'MT': return {'M', 'T'}
        if turno == 'TNN': return {'TN', 'N'}
        return set()

    mix_count = 0
    grouped = df_long.groupby(['Persona', 'Semana'])
    for (persona, semana), group in grouped:
        all_families = set()
        for _, row in group.iterrows():
            fams = get_families(row['Turno'])
            all_families.update(fams)
        
        # A mix occurs if they have more than one family in the same week
        if len(all_families) > 1:
            turnos_sem = list(group['Turno'])
            print(f"ALERTA: {persona} tiene mezcla de familias en la semana {semana}: {turnos_sem} (familias: {all_families})")
            mix_count += 1
            
    if mix_count == 0:
        print("EXITO: Nadie mezclo familias de turnos en la misma semana.")
    else:
        print(f"Total de mezclas encontradas: {mix_count}")

if __name__ == '__main__':
    check_nursing_mix()
