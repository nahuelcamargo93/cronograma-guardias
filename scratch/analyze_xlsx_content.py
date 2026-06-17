import pandas as pd
import openpyxl

file_name = "para_importar_kineJunio.xlsx"

def run():
    df = pd.read_excel(file_name)
    print("Shape:", df.shape)
    
    # Filtrar columnas que correspondan a junio (mes 6 del 2026)
    date_cols = []
    for col in df.columns:
        if isinstance(col, (pd.Timestamp, str)) or type(col).__name__ == 'datetime':
            try:
                dt = pd.to_datetime(col)
                if dt.year == 2026 and dt.month == 6:
                    date_cols.append(col)
            except:
                pass
                
    print(f"Columnas encontradas para Junio 2026: {len(date_cols)}")
    if date_cols:
        print(f"Desde {min(date_cols)} hasta {max(date_cols)}")
        
        # Veamos cuáles son los turnos que aparecen en la columna 'Turno'
        print("Valores únicos en 'Turno':")
        print(df['Turno'].unique())
        
        # Veamos las filas y las asignaciones para Junio 2026
        # Seleccionamos las columnas de Junio y la columna Turno
        sub_df = df[['Turno'] + date_cols]
        # Mostramos filas no vacías en esas fechas
        print("\nEjemplo de asignaciones en las fechas de Junio (primeras 10 filas):")
        print(sub_df.head(10).to_string())
        
        # Queremos saber el rango exacto de fechas que tienen asignaciones en junio
        has_assignments = []
        for col in date_cols:
            non_na = df[col].dropna().tolist()
            if non_na:
                has_assignments.append(col)
        print(f"\nColumnas de Junio con asignaciones reales ({len(has_assignments)}):")
        if has_assignments:
            print(f"Desde {min(has_assignments)} hasta {max(has_assignments)}")
            
            # Ver qué personas aparecen asignadas en junio
            all_people = set()
            for col in has_assignments:
                all_people.update(df[col].dropna().unique())
            print("Personas asignadas en Junio:", sorted(list(all_people)))

if __name__ == '__main__':
    run()
