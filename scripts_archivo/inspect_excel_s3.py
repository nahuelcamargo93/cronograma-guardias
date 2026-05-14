import pandas as pd

def inspect_excel():
    file = 'Cronograma_Area_Medica_UTI.xlsx'
    df = pd.read_excel(file, sheet_name='Cronograma')
    # Las columnas desde la segunda en adelante son fechas
    fechas = df.columns[1:]
    
    print(f"{'Fecha':<12} | {'Personas G':<12} | {'Personas D':<12} | {'Personas N':<12}")
    print("-" * 60)
    
    for fecha in fechas[:7]: # Ver primer semana
        col_data = df[fecha].dropna()
        # Contar por etiqueta de bloque (la columna 0 es 'Bloque')
        count_g = len(df[(df['Bloque'] == 'G') & (df[fecha].notna())])
        count_d = len(df[(df['Bloque'] == 'D') & (df[fecha].notna())])
        count_n = len(df[(df['Bloque'] == 'N') & (df[fecha].notna())])
        
        print(f"{str(fecha)[:10]:<12} | {count_g:<12} | {count_d:<12} | {count_n:<12}")

if __name__ == "__main__":
    inspect_excel()
