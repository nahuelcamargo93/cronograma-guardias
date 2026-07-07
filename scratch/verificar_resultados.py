import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

# Obtener el último cronograma id insertado de Agosto 2026 sin condicionar servicio_id
cursor.execute("""
    SELECT id, fecha_inicio, fecha_fin, notas, creado_en 
    FROM cronogramas 
    WHERE fecha_inicio = '2026-08-01'
    ORDER BY id DESC 
    LIMIT 1
""")
crono = cursor.fetchone()

if not crono:
    print("No se encontró ningún cronograma para Agosto 2026.")
    conn.close()
    exit(1)

crono_id, fi, ff, notas, creado = crono
print(f"=== Ultimo Cronograma Encontrado ===")
print(f"ID: {crono_id} | Rango: {fi} a {ff} | Notas: {notas} | Creado: {creado}")

toledo_nombre = "Toledo, Andrea"
garcia_nombre = "Garcia, Luciano"

# 1. Verificar Toledo Andrea (Franco forzado del 8 al 11 de agosto)
print(f"\n=== Guardias asignadas a {toledo_nombre} ===")
cursor.execute("""
    SELECT fecha, turno 
    FROM guardias 
    WHERE cronograma_id = ? AND nombre = ?
    ORDER BY fecha
""", (crono_id, toledo_nombre))
toledo_guardias = cursor.fetchall()
for g in toledo_guardias:
    fecha_str, turno = g
    status = ""
    if "2026-08-08" <= fecha_str <= "2026-08-11":
        status = " (!!! COLISION CON FRANCO FORZADO !!!)"
    print(f"Fecha: {fecha_str} | Turno: {turno}{status}")

# 2. Verificar Garcia Luciano (Franco forzado del 14 al 17 de agosto)
print(f"\n=== Guardias asignadas a {garcia_nombre} ===")
cursor.execute("""
    SELECT fecha, turno 
    FROM guardias 
    WHERE cronograma_id = ? AND nombre = ?
    ORDER BY fecha
""", (crono_id, garcia_nombre))
garcia_guardias = cursor.fetchall()
for g in garcia_guardias:
    fecha_str, turno = g
    status = ""
    if "2026-08-14" <= fecha_str <= "2026-08-17":
        status = " (!!! COLISION CON FRANCO FORZADO !!!)"
    print(f"Fecha: {fecha_str} | Turno: {turno}{status}")

# 3. Comprobar si hay alguna colisión
toledo_colisiones = [g for g in toledo_guardias if "2026-08-08" <= g[0] <= "2026-08-11"]
garcia_colisiones = [g for g in garcia_guardias if "2026-08-14" <= g[0] <= "2026-08-17"]

print("\n=== Resumen de Validacion de Prioridades ===")
if not toledo_colisiones:
    print(f"OK - {toledo_nombre}: Sin colisiones en su franco forzado (8 al 11 de agosto).")
else:
    print(f"ERROR - {toledo_nombre}: Colisiones detectadas: {toledo_colisiones}")

if not garcia_colisiones:
    print(f"OK - {garcia_nombre}: Sin colisiones en su franco forzado (14 al 17 de agosto).")
else:
    print(f"ERROR - {garcia_nombre}: Colisiones detectadas: {garcia_colisiones}")

conn.close()
