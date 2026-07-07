import sqlite3
import os

db_path = "c:\\Users\\asus\\Desktop\\Ryoko\\cronograma_inteligente\\cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== DIAS HABILITADOS POR TURNO ===")
rows_t = cursor.execute("""
    SELECT tc.nombre, tc.dias_semana, p.nombre
    FROM turnos_config tc
    LEFT JOIN puestos p ON tc.puesto_id = p.id
    WHERE tc.servicio_id = 3 AND tc.activo = 1
""").fetchall()
for r in rows_t:
    print(f"Turno: {r[0]:<20} | Dias Habilitados: {r[1]:<15} | Puesto: {r[2]}")

print("\n=== FERIADOS REGISTRADOS EN JULIO 2026 ===")
rows_f = cursor.execute("""
    SELECT fecha, descripcion
    FROM feriados
    WHERE fecha BETWEEN '2026-07-01' AND '2026-07-31'
""").fetchall()
for r in rows_f:
    print(f"Feriado: {r[0]} - {r[1]}")

conn.close()
