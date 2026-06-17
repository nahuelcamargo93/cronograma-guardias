import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

def print_table_schema(table_name):
    print(f"\n--- Esquema de {table_name} ---")
    cursor.execute(f"PRAGMA table_info({table_name})")
    for r in cursor.fetchall():
        print(r)

print_table_schema("turnos_config")
print_table_schema("demanda_config")
print_table_schema("puestos")
print_table_schema("personal")

conn.close()
