import sqlite3
import os

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def print_table_info(table_name):
    print(f"\n--- Columns in {table_name} ---")
    cursor.execute(f"PRAGMA table_info({table_name});")
    for col in cursor.fetchall():
        print(col)

print_table_info("personal")
print_table_info("turnos_config")
print_table_info("servicios")

print("\n--- SERVICIOS ---")
cursor.execute("SELECT * FROM servicios;")
for row in cursor.fetchall():
    print(row)

print("\n--- EMPLEADOS CON ROL O NOMBRE (primeros 20 de servicio_id 3 si existe la columna, o todos) ---")
# Let's inspect the columns of personal first so we can query correctly
cursor.execute("PRAGMA table_info(personal);")
cols = [col[1] for col in cursor.fetchall()]
query_cols = ", ".join([c for c in ["nombre", "rol", "servicio_id", "activo"] if c in cols])
if query_cols:
    cursor.execute(f"SELECT {query_cols} FROM personal WHERE servicio_id = 3;")
    for row in cursor.fetchall():
        print(row)

conn.close()
