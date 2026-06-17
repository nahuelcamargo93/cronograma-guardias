import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- PERSONAL DEL SERVICIO 1 ---")
rows_p = cursor.execute("""
SELECT nombre, rol, categoria, horas_mensuales_reglamentarias, activo
FROM personal
WHERE servicio_id = 1
""").fetchall()
for r in rows_p:
    print(f"Nombre: {r[0]}, Rol: {r[1]}, Cat: {r[2]}, Horas: {r[3]}, Activo: {r[4]}")

print("\n--- LICENCIAS SERVICIO 1 (JUNIO Y JULIO 2026) ---")
rows_l = cursor.execute("""
SELECT l.nombre, l.tipo, l.fecha_inicio, l.fecha_fin, l.metadata
FROM licencias l
JOIN personal p ON l.nombre = p.nombre
WHERE p.servicio_id = 1 
  AND (
      (l.fecha_inicio <= '2026-07-31' AND l.fecha_fin >= '2026-06-01')
  )
""").fetchall()
for r in rows_l:
    print(f"Nombre: {r[0]}, Tipo: {r[1]}, Inicio: {r[2]}, Fin: {r[3]}, Metadata: {r[4]}")

conn.close()
