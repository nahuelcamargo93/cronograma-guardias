import sqlite3
import sys
import os

sys.path.append(os.path.abspath('.'))

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Check Nuñez
cur.execute("SELECT nombre, activo FROM personal WHERE nombre LIKE '%Florencia%'")
row = cur.fetchone()
print(f"Nuñez status in DB: {row}")

# Check Adjustment 1364
cur.execute("SELECT id, personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, activo FROM personal_reglas_ajustes WHERE id = 1364")
row = cur.fetchone()
print(f"Adjustment 1364 in DB: {row}")

conn.close()

# Run main.py and print its output
print("\n--- Running main.py ---")
import main
res = main.ejecutar_optimizacion(3, "2026-06-01", "2026-06-30", "Test run after deactivating Biscarra FF")
print(f"Result: {res}")
