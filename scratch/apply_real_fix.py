import sqlite3
import os
import sys

sys.path.append(os.path.abspath('.'))
db_path = "cronograma_inteligente.db"

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get all active Planta doctors for service 3
cur.execute("SELECT nombre FROM personal WHERE servicio_id = 3 AND rol != 'Residente' AND COALESCE(activo, 1) = 1")
planta_names = [r[0] for r in cur.fetchall()]

print(f"Applying adjustments in real DB for {len(planta_names)} Planta doctors...")
inserted_count = 0
for name in planta_names:
    for rule in ['MIN_FINDES_MES', 'EXACTO_FINDES_MES']:
        # Check if adjustment already exists
        cur.execute("""
            SELECT id FROM personal_reglas_ajustes 
            WHERE personal_nombre = ? AND codigo_regla = ? AND fecha_inicio = '2026-06-01' AND fecha_fin = '2026-06-30' AND accion = 'SUSPENDER' AND activo = 1
        """, (name, rule))
        if cur.fetchone() is None:
            cur.execute("""
                INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
                VALUES (?, ?, '2026-06-01', '2026-06-30', 'SUSPENDER', '[]', 1)
            """, (name, rule))
            inserted_count += 1

conn.commit()
conn.close()
print(f"Inserted {inserted_count} new adjustment rows in personal_reglas_ajustes.")

# Run the real solver optimization
import database.connection as db_conn
db_conn.DB_PATH = os.path.abspath(db_path)

import importlib
import database.queries as db_queries
importlib.reload(db_queries)
import database.data_loader as dl
importlib.reload(dl)
import main
importlib.reload(main)

print("Starting optimizer on real database...")
res = main.ejecutar_optimizacion(3, "2026-06-01", "2026-06-30", "Junio 2026 sin Nunez (con suspension de reglas de finde para Planta)")
print(f"Solver Result: {res}")
