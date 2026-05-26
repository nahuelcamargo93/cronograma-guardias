import pandas as pd
excel_path = "para_importar_enfermeria.xlsx"
df = pd.read_excel(excel_path, sheet_name="JUNIO 26", header=None)
print("Shape:", df.shape)
print("First 10 rows of columns 0, 1, 2, 3, 4:")
print(df.iloc[:10, :5].to_string())

# Check if there are any non-null values in column 1 and column 2
print("\nNon-null values in Column 1:", df[1].dropna().tolist()[:10])
print("Non-null values in Column 2:", df[2].dropna().tolist()[:10])
