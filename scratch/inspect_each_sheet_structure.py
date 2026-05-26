import pandas as pd

excel_path = "para_importar_enfermeria.xlsx"
xl = pd.ExcelFile(excel_path)

for sheet in xl.sheet_names:
    print(f"\n======================================")
    print(f"SHEET: {sheet}")
    print(f"======================================")
    df = xl.parse(sheet, header=None)
    
    # Print the first few columns and rows in detail
    print(f"Shape: {df.shape}")
    
    # Print row 0 and row 1 completely
    print("Row 0:")
    print(list(df.iloc[0]))
    if df.shape[0] > 1:
        print("Row 1:")
        print(list(df.iloc[1]))
        print("Row 2:")
        print(list(df.iloc[2]))
        
    # Let's print non-null values of the first column (potential names)
    names_col = df.iloc[:, 0].dropna()
    print(f"First column non-null count: {len(names_col)}")
    print("First 5 non-null values in column 0:", list(names_col[:5]))
    print("Last 5 non-null values in column 0:", list(names_col[-5:]))
