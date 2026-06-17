import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

print("--- REGLAS DE SERVICIO 3 EN CATALOGO ---")
rows_cat = cursor.execute("SELECT * FROM reglas_catalogo WHERE codigo_regla LIKE '%DESCANSO%'").fetchall()
for r in rows_cat:
    print(r)

print("\n--- REGLAS EN servicios_reglas PARA SERVICIO 3 ---")
rows_sr = cursor.execute("SELECT * FROM servicios_reglas WHERE servicio_id = 3").fetchall()
for r in rows_sr:
    print(r)

print("\n--- AJUSTES EN servicios_reglas_ajustes PARA SERVICIO 3 ---")
rows_sra = cursor.execute("SELECT * FROM servicios_reglas_ajustes WHERE servicio_id = 3").fetchall()
for r in rows_sra:
    print(r)

conn.close()
