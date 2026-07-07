import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
for table in ['demanda_config', 'turnos_config', 'demanda_ajustes', 'turnos_ajustes']:
    cursor = conn.execute(f"SELECT * FROM {table} LIMIT 1")
    names = [description[0] for description in cursor.description]
    print(f"Table {table}: {names}")
conn.close()
