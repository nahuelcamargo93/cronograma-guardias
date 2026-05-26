import pandas as pd

excel_path = "para_importar_enfermeria.xlsx"
xl = pd.ExcelFile(excel_path)

for sheet in xl.sheet_names:
    df = xl.parse(sheet, header=None)
    for r in range(df.shape[0]):
        for c in range(df.shape[1]):
            val = df.iloc[r, c]
            if pd.notna(val) and str(val).strip().upper() in ["C", "CM"]:
                print(f"Sheet: {sheet} | Row: {r} | Col: {c} | Name: {df.iloc[r, 0]} | Val: {val}")
