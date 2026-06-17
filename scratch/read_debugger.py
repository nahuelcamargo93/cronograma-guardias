import pandas as pd
excel_file = "cronograma_debugger_Enfermeria_UTI_Julio26.xlsx"
df = pd.read_excel(excel_file, sheet_name=0)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', None)
print(df)
