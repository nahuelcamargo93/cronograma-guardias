import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

# 1. Ver si alguien tiene FCG como asignacion fija para agosto
print('=== ASIGNACIONES FIJAS CON FCG (agosto 2026) ===')
cur.execute("""
SELECT personal_nombre, fecha, dia_semana, turno, activo
FROM personal_asignaciones_fijas
WHERE (turno = 'FCG') AND activo = 1
""")
rows = cur.fetchall()
print(f'Total: {len(rows)}')
for r in rows: print(r)

# 2. Ver ajustes de reglas personales con FCG para agosto
print()
print('=== AJUSTES TEMPORALES CON FCG (agosto 2026) ===')
cur.execute("""
SELECT personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json
FROM personal_reglas_ajustes
WHERE parametros_json LIKE '%FCG%' AND activo = 1
AND fecha_inicio <= '2026-08-31' AND fecha_fin >= '2026-08-01'
""")
rows = cur.fetchall()
print(f'Total: {len(rows)}')
for r in rows: print(r)

# 3. Ver el estado actual de POLETTI
print()
print('=== POLETTI - TODAS SUS REGLAS PERSONALES ===')
cur.execute("""
SELECT codigo_regla, activo, parametros_json
FROM personal_reglas
WHERE personal_nombre = 'POLETTI NATALIA' AND activo = 1
""")
for r in cur.fetchall():
    print(r)

# 4. Ver si FCG tiene demanda configurada (que el solver deba cubrir)
print()
print('=== DEMANDA CONFIG PARA EL TURNO FCG (puesto 9) ===')
cur.execute("""
SELECT dc.*, p.nombre as puesto_nombre
FROM demanda_config dc
JOIN puestos p ON dc.puesto_id = p.id
WHERE dc.puesto_id = 9 AND dc.activo = 1
""")
for r in cur.fetchall():
    print(r)

# 5. Verificar si la exclusion de servicio actual para FCG es correcta
print()
print('=== EXCLUIR_TURNOS A NIVEL SERVICIO 2 ===')
cur.execute("SELECT id, parametros_json FROM servicios_reglas WHERE servicio_id=2 AND codigo_regla='EXCLUIR_TURNOS'")
for r in cur.fetchall():
    print(r)

conn.close()
