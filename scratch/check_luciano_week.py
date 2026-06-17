import sqlite3
import datetime

conn = sqlite3.connect("cronograma_inteligente.db")
crono_id = 438

# Check feriados in the crono range
crono = conn.execute("SELECT fecha_inicio, fecha_fin FROM cronogramas WHERE id = ?", (crono_id,)).fetchone()
fecha_inicio, fecha_fin = crono[0], crono[1]

print("=== FERIADOS ===")
feriados = conn.execute("SELECT fecha, descripcion FROM feriados WHERE fecha BETWEEN ? AND ?", (fecha_inicio, fecha_fin)).fetchall()
for f in feriados:
    print(f"  {f[0]}: {f[1]}")

print("\n=== LICENCIAS DE JEFES Y COORDINADORES ===")
names = ["Garcia, Luciano", "Toledo, Andrea", "Franco, Leandro", "Moyano, Fernando"]
placeholders = ",".join("?" for _ in names)
lics = conn.execute(f"SELECT nombre, tipo, fecha_inicio, fecha_fin FROM licencias WHERE nombre IN ({placeholders}) AND fecha_inicio <= ? AND fecha_fin >= ?", names + [fecha_fin, fecha_inicio]).fetchall()
for l in lics:
    print(f"  {l[0]}: {l[1]} ({l[2]} a {l[3]})")

print("\n=== DETALLE DE LA SEMANA JUL 6 - JUL 12 PARA Garcia, Luciano ===")
# Let's see what guards are assigned to him in that week
guards = conn.execute("SELECT fecha, turno FROM guardias WHERE cronograma_id = ? AND nombre = 'Garcia, Luciano' AND fecha BETWEEN '2026-07-06' AND '2026-07-12'", (crono_id,)).fetchall()
for g in guards:
    print(f"  Guardia: {g[0]} ({g[1]})")

# Let's check if he has any EXCLUIR_TURNOS or other rules affecting that week
print("\n=== REGLAS INDIVIDUALES DE Garcia, Luciano ===")
rules = conn.execute("SELECT codigo_regla, parametros_json, activo FROM personal_reglas WHERE personal_nombre = 'Garcia, Luciano'").fetchall()
for r in rules:
    print(f"  {r[0]} (Activo: {r[2]}): {r[1]}")

conn.close()
