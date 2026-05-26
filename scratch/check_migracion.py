import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("--- ESTRUCTURA DE TABLA: organizaciones_reglas ---")
print(pd.read_sql_query("PRAGMA table_info(organizaciones_reglas);", conn))

print("\n--- ESTRUCTURA DE TABLA: servicios_reglas ---")
print(pd.read_sql_query("PRAGMA table_info(servicios_reglas);", conn))

print("\n--- ESTRUCTURA DE TABLA: personal_reglas ---")
print(pd.read_sql_query("PRAGMA table_info(personal_reglas);", conn))

print("\n--- EJEMPLO DE DATOS EN servicios_reglas ---")
print(pd.read_sql_query("SELECT * FROM servicios_reglas LIMIT 5;", conn))

print("\n--- EJEMPLO DE DATOS EN personal_reglas ---")
print(pd.read_sql_query("SELECT * FROM personal_reglas LIMIT 5;", conn))

# Check foreign key constraint status
print("\n--- CHEQUEO DE FOREIGN KEYS ---")
fk_list = conn.execute("PRAGMA foreign_key_check;").fetchall()
if fk_list:
    print("ERRORES DE CONFLICTO DE CLAVE FORÁNEA ENCONTRADOS:")
    for fk in fk_list:
        print(fk)
else:
    print("No se encontraron conflictos de clave foránea. ¡Esquema íntegro!")

conn.close()
