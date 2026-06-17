import sqlite3
import json
import datetime

conn = sqlite3.connect("cronograma_inteligente.db")
crono_id = 438

print("=== CRONOGRAMA DETALLES ===")
crono = conn.execute("SELECT id, fecha_inicio, fecha_fin, notas, estado FROM cronogramas WHERE id = ?", (crono_id,)).fetchone()
print(crono)

if crono:
    fecha_inicio, fecha_fin = crono[1], crono[2]
else:
    # If 438 doesn't exist, let's find the latest cronograma
    print("Cronograma 438 no encontrado. Últimos cronogramas:")
    for row in conn.execute("SELECT id, fecha_inicio, fecha_fin, notas, estado FROM cronogramas ORDER BY id DESC LIMIT 5").fetchall():
        print(row)
    # Let's use the latest one as crono_id
    latest = conn.execute("SELECT id, fecha_inicio, fecha_fin, notas, estado FROM cronogramas ORDER BY id DESC LIMIT 1").fetchone()
    if latest:
        crono_id = latest[0]
        fecha_inicio, fecha_fin = latest[1], latest[2]
        print(f"Usando cronograma id={crono_id}")

print("\n=== PERSONAL DEL SERVICIO 1 ===")
personal = conn.execute("SELECT nombre, rol, activo, categoria FROM personal WHERE servicio_id = 1").fetchall()
for p in personal:
    print(f"Nombre: {p[0]}, Rol: {p[1]}, Activo: {p[2]}, Categoría: {p[3]}")

print("\n=== GUARDIAS EN FIN DE SEMANA CRONOGRAMA {} ===".format(crono_id))
rows = conn.execute(
    "SELECT nombre, fecha, turno FROM guardias WHERE cronograma_id = ?", (crono_id,)
).fetchall()

counts = {}
for name, f_str, turno in rows:
    dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
    wd = dt.weekday()
    if wd in (5, 6):
        counts.setdefault(name, []).append((f_str, wd, turno))

for name, rol, activo, _ in personal:
    if activo:
        shifts = counts.get(name, [])
        print(f"{name} (Rol: {rol}): {len(shifts)} guardias en fin de semana")
        for s in shifts:
            print(f"  {s[0]} (WD {s[1]}): {s[2]}")

print("\n=== REGLAS ACTIVAS PARA EL SERVICIO 1 ===")
rules_serv = conn.execute("SELECT codigo_regla, activo, parametros_json FROM servicios_reglas WHERE servicio_id = 1").fetchall()
for code, act, params in rules_serv:
    print(f"Regla: {code}, Activo: {act}")
    if code == 'MANEJO_FINDES':
        print(f"  Params: {params}")

print("\n=== REGLAS DE PERSONAL EN SERVICIO 1 (especialmente MANEJO_FINDES o similares) ===")
rules_pers = conn.execute(
    "SELECT pr.personal_nombre, p.rol, pr.codigo_regla, pr.activo, pr.parametros_json "
    "FROM personal_reglas pr "
    "JOIN personal p ON pr.personal_nombre = p.nombre "
    "WHERE p.servicio_id = 1 AND pr.activo = 1"
).fetchall()
for nom, rol, code, act, params in rules_pers:
    print(f"Empleado: {nom} ({rol}), Regla: {code}, Activo: {act}, Params: {params}")

print("\n=== PUESTOS HABILITADOS Y PRIMARIOS DE JEFES Y COORDINADORES ===")
puestos = conn.execute(
    "SELECT pp.personal_nombre, p.nombre, pp.es_primario "
    "FROM personal_puestos pp "
    "JOIN puestos p ON pp.puesto_id = p.id "
    "JOIN personal pers ON pp.personal_nombre = pers.nombre "
    "WHERE pers.servicio_id = 1"
).fetchall()
for name, puesto, es_prim in puestos:
    print(f"Empleado: {name}, Puesto: {puesto}, Es Primario: {es_prim}")

conn.close()
