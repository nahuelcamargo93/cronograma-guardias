import shutil
import sqlite3
import sys
import os

sys.path.append(os.path.abspath('.'))

# Copy the database
db_original = "cronograma_inteligente.db"
db_copy = "cronograma_inteligente_test.db"
shutil.copyfile(db_original, db_copy)
print(f"Copied {db_original} to {db_copy}")

# Connect to the copied database and find Nuñez
conn = sqlite3.connect(db_copy)
cur = conn.cursor()
cur.execute("SELECT nombre, activo FROM personal WHERE nombre LIKE '%Florencia%'")
row = cur.fetchone()
if not row:
    print("Employee Florencia not found in copy!")
    conn.close()
    sys.exit(1)
    
name = row[0]
print(f"Found employee in copy: {name} | Active: {row[1]}")

# Function to run diagnosis on the copy database
def run_diagnosis(nunez_active):
    # Set active status in the copy
    status = 1 if nunez_active else 0
    print(f"\n========================================\nDIAGNOSIS WITH NUÑEZ ACTIVE = {nunez_active}\n========================================")
    cur.execute("UPDATE personal SET activo = ? WHERE nombre = ?", (status, name))
    conn.commit()
    
    # Patch connection.py DB_PATH
    import database.connection as db_conn
    db_conn.DB_PATH = os.path.abspath(db_copy)
    
    # Reload queries to make sure it uses the patched DB path
    import importlib
    import database.queries as db_queries
    importlib.reload(db_queries)
    import database.data_loader as dl
    importlib.reload(dl)
    
    import scratch.diagnose_unsat as du
    importlib.reload(du)
    
    du.reportar_imposibilidad(3, "2026-06-01", "2026-06-30")

# Run with Nuñez inactive
run_diagnosis(nunez_active=False)

# Run with Nuñez active
run_diagnosis(nunez_active=True)

conn.close()
# Clean up
if os.path.exists(db_copy):
    os.remove(db_copy)
    print("\nRemoved copy database file.")
