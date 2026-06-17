import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== Detalles del Personal del Servicio 3 ===")
cursor.execute("SELECT nombre, regimen_trabajo, horas_mensuales_reglamentarias, activo FROM personal WHERE servicio_id = 3")
for r in cursor.fetchall():
    print(f"Nombre: {r[0]:<35} | Regimen: {str(r[1]):<10} | Horas Reg: {str(r[2]):<5} | Activo: {r[3]}")

conn.close()
