import pandas as pd

def check_export():
    file_path = 'scratch/Cronograma_Enfermeria_UTI_Julio26_Test.xlsx'
    
    # Read the whole sheet without headers
    df_vp = pd.read_excel(file_path, sheet_name='Vista Personal', header=None)
    
    # Header row containing day numbers (e.g. index 3 or 4)
    header_days = df_vp.iloc[3].tolist()
    print("Header Days row (idx 3):", header_days)
    
    for r_idx in range(len(df_vp)):
        row_vals = df_vp.iloc[r_idx].tolist()
        if str(row_vals[0]).strip() == "ABELENDA GRISELL":
            print(f"\n--- Found 'ABELENDA GRISELL' at row index {r_idx} ---")
            for col_idx, val in enumerate(row_vals):
                day_name = header_days[col_idx] if col_idx < len(header_days) else ""
                print(f"  Col {col_idx} (Day {day_name}): {val}")

if __name__ == '__main__':
    check_export()
