import sqlite3
import sys
import os

sys.path.append(os.path.abspath('.'))

# Temporarily activate Nuñez
conn = sqlite3.connect("cronograma_inteligente.db")
cur = conn.cursor()
cur.execute("SELECT nombre, activo FROM personal WHERE nombre LIKE '%Florencia%'")
row = cur.fetchone()
if not row:
    print("Employee Florencia not found!")
    conn.close()
    sys.exit(1)
    
name = row[0]
original_activo = row[1]
print(f"Found employee: {name} with original active status: {original_activo}")

print("Setting active status to 1...")
cur.execute("UPDATE personal SET activo = 1 WHERE nombre = ?", (name,))
conn.commit()

# Run the UNSAT diagnosis
try:
    import scratch.diagnose_unsat as du
    print("\n--- Running diagnosis with Nuñez active ---")
    du.reportar_imposibilidad(3, "2026-06-01", "2026-06-30")
finally:
    # Restore original status
    print("\nRestoring original active status...")
    cur.execute("UPDATE personal SET activo = ? WHERE nombre = ?", (original_activo, name))
    conn.commit()
    conn.close()
