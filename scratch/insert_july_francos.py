import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

adjustments = [
    ("ABELENDA GRISELL", "FRANCO_FORZADO", "2026-07-02", "2026-07-02", "SOBRESCRIBIR", "{}", 1, 2),
    ("ROJAS JULIANA", "FRANCO_FORZADO", "2026-07-09", "2026-07-12", "SOBRESCRIBIR", "{}", 1, 2),
    ("ESCUDERO SERGIO", "FRANCO_FORZADO", "2026-07-04", "2026-07-04", "SOBRESCRIBIR", "{}", 1, 2),
    ("ASTUDILLO MELINA", "FRANCO_FORZADO", "2026-07-09", "2026-07-12", "SOBRESCRIBIR", "{}", 1, 2),
    ("BASCUR ALEJANDRA", "FRANCO_FORZADO", "2026-07-31", "2026-07-31", "SOBRESCRIBIR", "{}", 1, 2),
]

print("--- Inserting adjustments ---")
inserted_ids = []
for row in adjustments:
    cursor.execute("""
        INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, row)
    inserted_ids.append(cursor.lastrowid)
    print(f"Inserted row for {row[0]} (ID: {cursor.lastrowid})")

conn.commit()

print("\n--- Verifying inserted rows ---")
for row_id in inserted_ids:
    cursor.execute("SELECT * FROM personal_reglas_ajustes WHERE id = ?", (row_id,))
    print(cursor.fetchone())

conn.close()
print("\nDone.")
