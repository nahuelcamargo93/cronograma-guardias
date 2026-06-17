import pandas as pd
excel_file = "cronograma_debugger_Enfermeria_UTI_Julio26.xlsx"
df = pd.read_excel(excel_file, sheet_name=0)
df_filtered = df[~df.astype(str).apply(lambda x: x.str.contains('COBERTURA_DINAMICA', case=False)).any(axis=1)]
print(df_filtered.head(100).to_string())
