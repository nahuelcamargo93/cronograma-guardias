import sqlite3
import json
import shutil
import os

db_file = "cronograma_inteligente.db"
temp_db = "cronograma_inteligente_temp.db"

print("Copying database to temp file...")
try:
    shutil.copy(db_file, temp_db)
    print("Copy successful. Connecting to temp database...")
    
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Disable MANEJO_FINDES
    cursor.execute(
        "UPDATE servicios_reglas SET activo = 0 WHERE servicio_id = 1 AND codigo_regla = 'MANEJO_FINDES'"
    )
    print(f"Deactivated MANEJO_FINDES: {cursor.rowcount} row(s)")

    # Delete existing PESO_EQUIDAD_FINDES_MENSUAL
    cursor.execute(
        "DELETE FROM servicios_reglas WHERE servicio_id = 1 AND codigo_regla = 'PESO_EQUIDAD_FINDES_MENSUAL'"
    )

    # Insert new rule
    params = {
        "peso": 5000,
        "tipo": "HISTORICA",
        "fecha_inicio": "2026-06-22"
    }
    cursor.execute(
        "INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo) VALUES (?, ?, ?, ?)",
        (1, "PESO_EQUIDAD_FINDES_MENSUAL", json.dumps(params), 1)
    )
    print(f"Activated PESO_EQUIDAD_FINDES_MENSUAL: {cursor.rowcount} row(s)")

    conn.commit()
    conn.close()
    print("Temp database updated successfully. Copying back to original...")
    
    # Try to overwrite the original database file
    shutil.copy(temp_db, db_file)
    print("Database overwritten successfully!")
    
    # Clean up temp file
    os.remove(temp_db)
    print("Cleanup successful!")
except Exception as e:
    print("Error during workaround:")
    import traceback
    traceback.print_exc()
    if os.path.exists(temp_db):
        os.remove(temp_db)
