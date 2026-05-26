import pandas as pd

excel_path = "para_importar_enfermeria.xlsx"
xl = pd.ExcelFile(excel_path)

for sheet in xl.sheet_names:
    df = xl.parse(sheet, header=None)
    names = []
    for r in range(df.shape[0]):
        val = df.iloc[r, 0]
        if pd.notna(val) and str(val).strip():
            names.append(str(val).strip().upper())
            
    print(f"Sheet: {sheet}")
    for name in ['ESCUDERO SERGIO', 'ESCUDERO YANET', 'LUCERO MATIAS', 'LUCERO SABRINA']:
        present = name in names
        print(f"  - {name}: {'PRESENT' if present else 'ABSENT'}")
