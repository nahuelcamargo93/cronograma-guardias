import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# 1. Licenses starting on 2026-06-01 end on 2026-06-14
cursor.execute("UPDATE licencias SET fecha_fin = '2026-06-14' WHERE fecha_inicio = '2026-06-01'")
print(f"Updated {cursor.rowcount} licenses starting on 2026-06-01 to end on 2026-06-14")

# 2. Licenses starting on 2026-06-15 now start on 2026-06-16
cursor.execute("UPDATE licencias SET fecha_inicio = '2026-06-16' WHERE fecha_inicio = '2026-06-15'")
print(f"Updated {cursor.rowcount} licenses starting on 2026-06-15 to start on 2026-06-16")

conn.commit()
conn.close()
