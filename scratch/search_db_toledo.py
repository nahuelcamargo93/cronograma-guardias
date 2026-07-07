import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')

tables = ['personal_reglas_ajustes', 'personal_reglas', 'roles_reglas', 'servicios_reglas']
for t in tables:
    print(f"\n--- Table: {t} ---")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {t}")
    for row in cursor.fetchall():
        row_str = str(row)
        if '2026-08-10' in row_str or 'Toledo' in row_str:
            print(row)

conn.close()
