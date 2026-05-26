import sys
sys.path.append('.')

import sqlite3
from database.schema import inicializar_db
from database.queries import obtener_personal_db

def test_activo_filtering():
    print("Initializing DB to run migrations...")
    inicializar_db()
    
    conn = sqlite3.connect('cronograma_inteligente.db')
    cur = conn.cursor()
    
    # Check if 'activo' column exists
    cur.execute("PRAGMA table_info(personal)")
    columns = [col[1] for col in cur.fetchall()]
    assert 'activo' in columns, "Error: 'activo' column was not added to the 'personal' table!"
    print("OK: 'activo' column exists in 'personal' table.")
    
    # Insert test employees
    print("Inserting test employees...")
    cur.execute("INSERT OR REPLACE INTO personal (nombre, rol, servicio_id, activo) VALUES (?, ?, ?, ?)",
                ('TEST_INACTIVO_XYZ', 'Rotativo', 2, 0))
    cur.execute("INSERT OR REPLACE INTO personal (nombre, rol, servicio_id, activo) VALUES (?, ?, ?, ?)",
                ('TEST_ACTIVO_XYZ', 'Rotativo', 2, 1))
    conn.commit()
    
    # Query staff
    print("Querying personnel list for servicio_id=2...")
    staff = obtener_personal_db(2)
    staff_names = [s['Nombre'] for s in staff]
    
    # Clean up test entries
    cur.execute("DELETE FROM personal WHERE nombre IN (?, ?)", ('TEST_INACTIVO_XYZ', 'TEST_ACTIVO_XYZ'))
    conn.commit()
    conn.close()
    
    # Validate results
    assert 'TEST_ACTIVO_XYZ' in staff_names, "Error: Active test employee was not returned!"
    assert 'TEST_INACTIVO_XYZ' not in staff_names, "Error: Inactive test employee was returned!"
    
    print("OK: Active employee is returned, inactive employee is successfully filtered out!")
    print("\nALL TEST VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_activo_filtering()
