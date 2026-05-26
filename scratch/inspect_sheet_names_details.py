import sqlite3
import pandas as pd

excel_path = "para_importar_enfermeria.xlsx"
xl = pd.ExcelFile(excel_path)

conn = sqlite3.connect("cronograma_inteligente.db")
db_names = sorted([row[0] for row in conn.execute("SELECT nombre FROM personal WHERE servicio_id = 2").fetchall()])
conn.close()

print("--- DB NAMES ---")
for idx, name in enumerate(db_names):
    print(f"{idx+1:02d}. {name}")

print("\n--- EXCEL NAMES BY SHEET ---")
for sheet in xl.sheet_names:
    df = xl.parse(sheet, header=None)
    start_row = 0
    for r in range(min(5, df.shape[0])):
        val = str(df.iloc[r, 0]).strip().upper()
        if "APELLIDO" in val or "NOMBRE" in val:
            start_row = r + 1
            break
            
    names = []
    for r in range(start_row, df.shape[0]):
        val = df.iloc[r, 0]
        if pd.notna(val) and str(val).strip():
            names.append(str(val).strip().upper())
            
    print(f"Sheet '{sheet}' has {len(names)} names (row start: {start_row}). First 5: {names[:5]}...")
