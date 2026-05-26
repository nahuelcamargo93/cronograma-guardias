import pandas as pd

excel_path = "Cronograma_Enfermeria_UTI.xlsx"
df_cron = pd.read_excel(excel_path, sheet_name="Cronograma")
print("=== Dates in Excel Cronograma Sheet ===")
columns = [col for col in df_cron.columns if col != 'Turno']
print("First 5 columns:", columns[:5])
print("Last 5 columns:", columns[-5:])

df_pers = pd.read_excel(excel_path, sheet_name="Vista por Personal")
print("\n=== Columns in Vista por Personal Sheet ===")
print(df_pers.columns.tolist()[:10])
print(df_pers.columns.tolist()[-10:])

print("\n=== DOMINGUEZ VERONICA Row in Vista por Personal Sheet ===")
dominguez_row = df_pers[df_pers['ENFERMERO'] == 'DOMINGUEZ VERONICA']
print(dominguez_row.to_string())
