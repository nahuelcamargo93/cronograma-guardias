import db
conn = db.get_connection()
print("--- REGLAS DE MIN_TURNOS ---")
res = conn.execute("SELECT personal_nombre, parametros_json FROM personal_reglas WHERE regla_id = 64").fetchall()
for row in res:
    print(f"Personal: {row[0]} | Params: {row[1]}")

print("\n--- REGLAS DE EXCLUIR_TURNOS ---")
res = conn.execute("SELECT personal_nombre, parametros_json FROM personal_reglas WHERE regla_id = 4").fetchall()
for row in res:
    print(f"Personal: {row[0]} | Params: {row[1]}")
conn.close()
