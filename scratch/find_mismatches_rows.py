import sqlite3
import pandas as pd

excel_path = "para_importar_enfermeria.xlsx"
xl = pd.ExcelFile(excel_path)

conn = sqlite3.connect("cronograma_inteligente.db")
db_names = set(row[0] for row in conn.execute("SELECT nombre FROM personal WHERE servicio_id = 2").fetchall())
conn.close()

# List of mismatched names to inspect
mismatches = [
    'ABELENDA G', 'ABELENDA GRISEL', 'ALCARAZ FRANCISCO', 'BARROSO ERIKA',
    'BORIA MAIRA', 'CALDERON MJ', 'CARRERAS FAVIA', 'ESCUDERO YANET',
    'GOMEZ LOURDEZ', 'GRABOVIECKI', 'LUCERO SABRINA', 'PEREIRA CEISTINA',
    'GRUPO 3  TN-T -M-N', 'GRUPO 4 -T-M-N-TN-', 'N-TN-T-M    GRUPO 2'
]

for sheet in xl.sheet_names:
    df = xl.parse(sheet, header=None)
    start_row = 0
    for r in range(min(5, df.shape[0])):
        val = str(df.iloc[r, 0]).strip().upper()
        if "APELLIDO" in val or "NOMBRE" in val:
            start_row = r + 1
            break
            
    for r in range(start_row, df.shape[0]):
        val = df.iloc[r, 0]
        if pd.notna(val) and str(val).strip():
            name = str(val).strip().upper()
            if name in mismatches:
                print(f"Sheet: {sheet} | Row: {r} | Excel Name: '{name}' | First 5 values: {list(df.iloc[r, 1:6])}")
