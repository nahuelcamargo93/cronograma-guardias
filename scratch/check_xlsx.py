import pandas as pd

# Leer el Excel generado
# La hoja "Vista por Personal" contiene los totales por franja al final.
xls = pd.ExcelFile("Cronograma_Enfermeria_UTI_test.xlsx")
print("Hojas del Excel:", xls.sheet_names)

# Cargar la Vista por Personal
df_vista = pd.read_excel(xls, sheet_name="Vista por Personal")

# Buscar la fila que tiene "TOTAL N" en la primera columna (Enfermero o la columna del index)
print("\nBuscando filas de totales en Vista por Personal:")
# Imprimir las últimas 10 filas para ver los totales
print(df_vista.tail(10))

# Imprimir las columnas del 2026-07-01 para los totales
col_name = "2026-07-01"
if col_name in df_vista.columns:
    print(f"\nValores para la columna {col_name}:")
    for idx, row in df_vista.iterrows():
        # La primera columna suele ser el nombre del enfermero o la etiqueta
        first_val = row.iloc[0]
        if str(first_val).startswith("TOTAL") or str(first_val).strip() == "":
            print(f"{first_val}: {row[col_name]}")
else:
    print(f"\nLa columna {col_name} no existe. Columnas disponibles:")
    print(df_vista.columns)
