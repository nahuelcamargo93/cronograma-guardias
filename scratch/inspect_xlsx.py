import openpyxl
import pandas as pd

archivo = "archived_docs/para_importar_enfermeria.xlsx"
try:
    wb = openpyxl.load_workbook(archivo, read_only=True)
    print("Hojas en para_importar_enfermeria.xlsx:")
    print(wb.sheetnames)
except Exception as e:
    print("Error:", e)
