import sqlite3
import pandas as pd

def analyze():
    conn = sqlite3.connect('cronograma_inteligente.db')
    
    names = ['VERA JULIETA', 'CASTRO LUCIANO', 'ECHENIQUE ROCIO']
    print("--- LICENCIAS (desde tabla 'licencias') ---")
    for name in names:
        lics = pd.read_sql(f"SELECT * FROM licencias WHERE nombre = '{name}'", conn)
        print(f"{name}:\n{lics}")
        
    print("\n--- SHIFTS IN EXCEL ---")
    try:
        df_cron = pd.read_excel('Cronograma_Enfermeria_UTI.xlsx', sheet_name='Cronograma')
        for name in names:
            pers_df = df_cron[df_cron['Kinesiologo'] == name] # It's actually Enfermero but col name is Kinesiologo
            print(f"{name}: {len(pers_df)} shifts. Hours: {pers_df['Horas'].sum()}. Types: {pers_df['Turno'].unique()}")
    except Exception as e:
        print(f"Error reading Excel: {e}")
        
    conn.close()

if __name__ == "__main__":
    analyze()
