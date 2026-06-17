import pandas as pd

file_name = "para_importar_kineJunio.xlsx"

def run():
    df = pd.read_excel(file_name)
    
    # Obtener todas las columnas excepto 'Turno'
    cols = [col for col in df.columns if col != 'Turno']
    
    print("--- Fechas desde el 2026-05-20 en adelante en el Excel ---")
    for col in cols:
        try:
            dt = pd.to_datetime(col)
            if dt >= pd.to_datetime('2026-05-20'):
                non_na = df[col].dropna().count()
                print(f"Fecha: {dt.strftime('%Y-%m-%d')} ({dt.day_name()}) -> {non_na} asignaciones")
        except:
            pass

if __name__ == '__main__':
    run()
