import pandas as pd

def check_consistency(file_name='Cronograma_Servicio_Kinesiologia.xlsx'):
    # Leer el Excel (tenemos que transformarlo de nuevo a formato largo)
    df = pd.read_excel(file_name, sheet_name='Cronograma')
    
    # El Excel está en formato pivot, vamos a reconstruir los resultados
    # Columnas son Fecha, Indice es Turno
    results = []
    fechas = [c for c in df.columns if c != 'Turno']
    
    for _, row in df.iterrows():
        turno = str(row['Turno']).strip()
        for fecha in fechas:
            persona = row[fecha]
            if pd.notna(persona) and persona != "":
                results.append({'Fecha': fecha, 'Turno': turno, 'Persona': persona})
    
    df_long = pd.DataFrame(results)
    df_long['Fecha'] = pd.to_datetime(df_long['Fecha'])
    df_long['Semana'] = df_long['Fecha'].dt.isocalendar().week
    
    print("--- VERIFICACIÓN DE CONSISTENCIA ---")
    
    # 1. Mezcla Mañana/Tarde
    def get_momento(t):
        if 'Mañana' in t: return 'M'
        if 'Tarde' in t: return 'T'
        return 'O' # Otro (Noche, Dia)

    df_long['Momento'] = df_long['Turno'].apply(get_momento)
    
    mix_count = 0
    for (persona, semana), group in df_long.groupby(['Persona', 'Semana']):
        momentos = set(group[group['Momento'].isin(['M', 'T'])]['Momento'])
        if len(momentos) > 1:
            print(f"ALERTA: {persona} mezcla M y T en semana {semana}: {momentos}")
            mix_count += 1
    
    if mix_count == 0:
        print("EXITO: Nadie mezcla Mañana y Tarde en la misma semana.")
    
    # 2. Diversidad de tipos
    print("\n--- DIVERSIDAD DE TIPOS POR SEMANA ---")
    inconsistencias = 0
    for (persona, semana), group in df_long.groupby(['Persona', 'Semana']):
        # Solo L-V (Semana)
        lv_group = group[~group['Turno'].isin(['Dia_UTI', 'Dia_UCO', 'Noche'])]
        if not lv_group.empty:
            tipos = lv_group['Turno'].unique()
            if len(tipos) > 1:
                print(f"INFO: {persona} tiene {len(tipos)} tipos en semana {semana}: {list(tipos)}")
                inconsistencias += 1
    
    print(f"Total semanas con más de 1 tipo: {inconsistencias}")

    # 3. Giacoppo
    giac = df_long[df_long['Persona'] == 'Lic. Giaccoppo']
    print("\n--- SEGUIMIENTO GIACOPPO ---")
    for sem, group in giac.groupby('Semana'):
        lv_group = group[~group['Turno'].isin(['Dia_UTI', 'Dia_UCO', 'Noche'])]
        tipos = lv_group['Turno'].value_counts()
        if not tipos.empty:
            print(f"Semana {sem}: {tipos.to_dict()}")

if __name__ == "__main__":
    check_consistency()
