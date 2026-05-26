import sqlite3
import subprocess

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    # 1. Find the puesto_id for 'General' in service 1
    cursor.execute("SELECT id FROM puestos WHERE servicio_id = 1 AND nombre = 'General'")
    row = cursor.fetchone()
    if not row:
        print("Error: Could not find 'General' puesto for service 1.")
        return
    puesto_general_id = row[0]
    print(f"Found 'General' puesto_id: {puesto_general_id}")
    
    # 2. Find all staff in service 1 with category 'GENERAL'
    cursor.execute("SELECT nombre FROM personal WHERE servicio_id = 1 AND categoria = 'GENERAL'")
    staff_names = [r[0] for r in cursor.fetchall()]
    print(f"Found {len(staff_names)} staff members with category 'GENERAL'.")
    
    # 3. Add mapping to personal_puestos
    added_count = 0
    for name in staff_names:
        cursor.execute("INSERT OR IGNORE INTO personal_puestos (personal_nombre, puesto_id) VALUES (?, ?)", (name, puesto_general_id))
        if cursor.rowcount > 0:
            added_count += 1
            
    print(f"Added {added_count} mappings to personal_puestos.")
    conn.commit()
    conn.close()
    
    # 4. Run the debugger to see if it resolves the infeasibility
    print("Running debug_imposibilidad.py to test feasibility...")
    result = subprocess.run(["python", "debug_imposibilidad.py"], capture_output=True, text=True)
    print("=== DEBUG OUTPUT ===")
    print(result.stdout)
    if "EL MODELO ES FACTIBLE" in result.stdout:
        print("\n>>> SUCCESS: The model is now FEASIBLE!")
    else:
        print("\n>>> FAILED: The model is still INFEASIBLE.")

if __name__ == "__main__":
    main()
