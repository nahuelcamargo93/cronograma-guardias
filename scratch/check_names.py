import sqlite3
import pandas as pd

excel_path = "para_importar_enfermeria.xlsx"
xl = pd.ExcelFile(excel_path)

# Load database names
conn = sqlite3.connect("cronograma_inteligente.db")
db_names = set(row[0] for row in conn.execute("SELECT nombre FROM personal WHERE servicio_id = 2").fetchall())
conn.close()

print(f"Total database names for Enfermeria UTI: {len(db_names)}")

excel_names_all = set()
sheet_names_map = {}

# We'll extract names from row index 1 to the end (column 0)
for sheet in xl.sheet_names:
    df = xl.parse(sheet, header=None)
    # The first row with APELLIDO Y NOMBRE is either row 0 or row 1.
    # Let's find the start row by looking for 'APELLIDO Y NOMBRE' or 'APELLIDO'
    start_row = 0
    for r in range(min(5, df.shape[0])):
        val = str(df.iloc[r, 0]).strip().upper()
        if "APELLIDO" in val or "NOMBRE" in val:
            start_row = r + 1
            break
    
    sheet_names = []
    for r in range(start_row, df.shape[0]):
        val = df.iloc[r, 0]
        if pd.notna(val) and str(val).strip():
            name = str(val).strip().upper()
            sheet_names.append(name)
            excel_names_all.add(name)
            
    sheet_names_map[sheet] = sheet_names

print(f"Total unique names in Excel across all sheets: {len(excel_names_all)}")

print("\n--- Checking Mismatches ---")
not_in_db = excel_names_all - db_names
not_in_excel = db_names - excel_names_all

print(f"Names in Excel but not in DB ({len(not_in_db)}):")
for n in sorted(not_in_db):
    print(f"  - '{n}'")

print(f"\nNames in DB but not in Excel ({len(not_in_excel)}):")
for n in sorted(not_in_excel):
    print(f"  - '{n}'")
