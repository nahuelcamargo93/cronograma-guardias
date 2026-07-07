import pandas as pd

def check_crono():
    file_path = 'scratch/Cronograma_Enfermeria_UTI_Julio26_Test.xlsx'
    df_crono = pd.read_excel(file_path, sheet_name='Cronograma', header=None)
    days = df_crono.iloc[1].tolist()
    
    for day_str in ["14/7", "22/7"]:
        col_idx = None
        for i, d in enumerate(days):
            if str(d).strip() == day_str:
                col_idx = i
                break
                
        print(f"\nDay {day_str} column index: {col_idx}")
        if col_idx is not None:
            print(f"Rows on day {day_str}:")
            for r_idx in range(len(df_crono)):
                shift = df_crono.iloc[r_idx, 0]
                val = df_crono.iloc[r_idx, col_idx]
                if pd.notna(val) and any("ABELENDA" in str(v) for v in str(val).split("\n")):
                    print(f"  Row {r_idx} (Shift {shift}): {repr(val)}")

if __name__ == '__main__':
    check_crono()
