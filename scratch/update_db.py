import sqlite3
import json
import time

print("Connecting to database...")
try:
    conn = sqlite3.connect("cronograma_inteligente.db", timeout=30.0)
    conn.execute("PRAGMA busy_timeout = 30000") # 30 seconds
    
    # Check journal mode
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    print(f"Current journal mode: {mode}")
    
    cursor = conn.cursor()

    # Disable MANEJO_FINDES
    print("Updating MANEJO_FINDES...")
    cursor.execute(
        "UPDATE servicios_reglas SET activo = 0 WHERE servicio_id = 1 AND codigo_regla = 'MANEJO_FINDES'"
    )
    print(f"Deactivated MANEJO_FINDES: {cursor.rowcount} row(s)")

    # Delete existing PESO_EQUIDAD_FINDES_MENSUAL
    print("Deleting existing PESO_EQUIDAD_FINDES_MENSUAL...")
    cursor.execute(
        "DELETE FROM servicios_reglas WHERE servicio_id = 1 AND codigo_regla = 'PESO_EQUIDAD_FINDES_MENSUAL'"
    )

    # Insert new rule
    print("Inserting PESO_EQUIDAD_FINDES_MENSUAL...")
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

    print("Committing transaction...")
    conn.commit()
    conn.close()
    print("Database update completed successfully!")
except Exception as e:
    print("Error during database update:", e)
    import traceback
    traceback.print_exc()
