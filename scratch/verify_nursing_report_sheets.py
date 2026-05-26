import openpyxl
import pandas as pd
import sys

def verify_report(file_path="Cronograma_Enfermeria_UTI.xlsx"):
    print(f"Loading workbook: {file_path}")
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
    except Exception as e:
        print(f"ERROR: Could not load workbook: {e}")
        return False
        
    sheet_names = wb.sheetnames
    print(f"Sheets in workbook: {sheet_names}")
    
    expected_sheets = ["Reporte Julio 2026", "Reporte historico"]
    for es in expected_sheets:
        if es not in sheet_names:
            print(f"ERROR: Expected sheet '{es}' not found in workbook.")
            return False
        print(f"OK: Sheet '{es}' found.")
        
    expected_columns = ["Nombre", "Horas Totales", "FS habiles", "FS trabajado", "1/2 FS trabajado", "Feriados"]
    
    all_ok = True
    for sheet_name in expected_sheets:
        print(f"\n--- Verifying Sheet: {sheet_name} ---")
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        cols = list(df.columns)
        print(f"Columns: {cols}")
        if cols != expected_columns:
            print(f"ERROR: Columns in '{sheet_name}' do not match expected.")
            print(f"Expected: {expected_columns}")
            print(f"Got:      {cols}")
            all_ok = False
        else:
            print(f"OK: Columns in '{sheet_name}' match expected perfectly.")
            
        print("Data Preview:")
        print(df.to_string(index=False))
        
    return all_ok

if __name__ == "__main__":
    success = verify_report()
    sys.exit(0 if success else 1)
