import pandas as pd
excel_path = "para_importar_enfermeria.xlsx"
df = pd.read_excel(excel_path, sheet_name="ENERO 26 ")
print("Columns:")
print(list(df.columns))
print("First row values:")
print(list(df.iloc[0]))
