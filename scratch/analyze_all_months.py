import pandas as pd
import collections

file_name = "para_importar_kineJunio.xlsx"

def run():
    df = pd.read_excel(file_name)
    
    monthly_counts = collections.defaultdict(int)
    
    for col in df.columns:
        if col == 'Turno':
            continue
        try:
            dt = pd.to_datetime(col)
            non_na_count = df[col].dropna().count()
            month_str = dt.strftime('%Y-%m')
            monthly_counts[month_str] += non_na_count
        except Exception as e:
            pass
            
    print("--- Cantidad de asignaciones por mes en Excel ---")
    for m, count in sorted(monthly_counts.items()):
        print(f"Mes: {m} -> {count} asignaciones")

if __name__ == '__main__':
    run()
