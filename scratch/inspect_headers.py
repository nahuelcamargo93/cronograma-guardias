import pandas as pd

excel_path = "para_importar_enfermeria.xlsx"
xl = pd.ExcelFile(excel_path)

for sheet in xl.sheet_names:
    print(f"\n======================================")
    print(f"SHEET: {sheet}")
    print(f"======================================")
    df = xl.parse(sheet, header=None) # Load without header to inspect raw rows
    print(f"Raw shape: {df.shape}")
    print("First 4 rows, first 10 columns:")
    print(df.iloc[:4, :10].to_string())
