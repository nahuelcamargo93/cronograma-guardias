import pandas as pd
import openpyxl

excel_path = "para_importar_enfermeria.xlsx"
xl = pd.ExcelFile(excel_path)
print("Sheet names:", xl.sheet_names)

for sheet in xl.sheet_names[:3]:
    print(f"\n--- Sheet: {sheet} ---")
    df = xl.parse(sheet)
    print("Columns:", list(df.columns)[:10])
    print("Shape:", df.shape)
    print("First 5 rows:")
    print(df.head(5))
