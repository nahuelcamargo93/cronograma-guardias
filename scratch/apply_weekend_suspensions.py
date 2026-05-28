import sqlite3
import shutil
import os
import sys

sys.path.append(os.path.abspath('.'))
db_original = "cronograma_inteligente.db"
db_copy = "cronograma_inteligente_test.db"

if os.path.exists(db_copy):
    try: os.remove(db_copy)
    except: pass
shutil.copyfile(db_original, db_copy)

# Connect to copy database
conn = sqlite3.connect(db_copy)
cur = conn.cursor()

# Get all active Planta doctors for service 3
cur.execute("SELECT nombre FROM personal WHERE servicio_id = 3 AND rol != 'Residente' AND COALESCE(activo, 1) = 1")
planta_names = [r[0] for r in cur.fetchall()]

print(f"Suspending weekend rules for {len(planta_names)} Planta doctors...")
for name in planta_names:
    # Check if they already have a suspension in June to avoid duplicates
    for rule in ['MIN_FINDES_MES', 'EXACTO_FINDES_MES']:
        cur.execute("""
            SELECT id FROM personal_reglas_ajustes 
            WHERE personal_nombre = ? AND codigo_regla = ? AND fecha_inicio = '2026-06-01' AND fecha_fin = '2026-06-30' AND accion = 'SUSPENDER' AND activo = 1
        """, (name, rule))
        if cur.fetchone() is None:
            cur.execute("""
                INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
                VALUES (?, ?, '2026-06-01', '2026-06-30', 'SUSPENDER', '[]', 1)
            """, (name, rule))

conn.commit()
conn.close()

# Test solve using the copy database
import database.connection as db_conn
db_conn.DB_PATH = os.path.abspath(db_copy)

import importlib
import database.queries as db_queries
importlib.reload(db_queries)
import database.data_loader as dl
importlib.reload(dl)
import main
importlib.reload(main)

print("Solving using main.ejecutar_optimizacion...")
res = main.ejecutar_optimizacion(3, "2026-06-01", "2026-06-30", "Test run with weekend suspensions for Planta")
print(f"Result: {res}")

if os.path.exists(db_copy):
    try: os.remove(db_copy)
    except: pass
