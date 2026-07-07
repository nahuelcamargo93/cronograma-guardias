import sqlite3
import json

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if rule exists
rows = cursor.execute(
    "SELECT id, codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 4 AND codigo_regla = 'PESO_EQUIDAD_FINDES_MENSUAL'"
).fetchall()
print("Registros existentes:", rows)

# Insert if needed
if not rows:
    cursor.execute(
        "INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo) VALUES (4, 'PESO_EQUIDAD_FINDES_MENSUAL', ?, 1)",
        (json.dumps({"peso": 20000}),)
    )
    print("Insertado nuevo registro con peso=20000")
else:
    # Hay registro con activo=0?
    inactive = [r for r in rows if r[3] == 0]
    active = [r for r in rows if r[3] == 1]
    if active:
        cursor.execute(
            "UPDATE servicios_reglas SET parametros_json = ? WHERE id = ?",
            (json.dumps({"peso": 20000}), active[0][0])
        )
        print(f"Actualizado registro existente id={active[0][0]} a peso=20000")
    elif inactive:
        # activar y actualizar
        cursor.execute(
            "UPDATE servicios_reglas SET parametros_json = ?, activo = 1 WHERE id = ?",
            (json.dumps({"peso": 20000}), inactive[0][0])
        )
        print(f"Activado y actualizado registro id={inactive[0][0]} a peso=20000")

conn.commit()

# Verificación final
print("\n--- Verificación ---")
all_rows = cursor.execute(
    "SELECT id, codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 4 AND codigo_regla = 'PESO_EQUIDAD_FINDES_MENSUAL'"
).fetchall()
for row in all_rows:
    print(row)

conn.close()
