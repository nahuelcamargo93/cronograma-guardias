import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cronograma_id = 252

print("=== ASIGNACIONES DE PLANTA DEL 20 AL 27 DE JULIO ===")
cursor.execute("""
    SELECT fecha, turno, nombre 
    FROM guardias 
    WHERE cronograma_id = ? AND fecha BETWEEN '2026-07-20' AND '2026-07-27'
      AND (turno LIKE '%Planta%')
    ORDER BY fecha, turno
""", (cronograma_id,))
for g in cursor.fetchall():
    print(g)

# Ver las licencias de TODO el personal en ese rango para ver si faltaba gente
print("\n=== LICENCIAS ACTIVAS DEL 20 AL 27 DE JULIO ===")
cursor.execute("""
    SELECT nombre, tipo, fecha_inicio, fecha_fin 
    FROM licencias 
    WHERE (fecha_inicio BETWEEN '2026-07-20' AND '2026-07-27')
       OR (fecha_fin BETWEEN '2026-07-20' AND '2026-07-27')
       OR (fecha_inicio <= '2026-07-20' AND fecha_fin >= '2026-07-27')
""")
for l in cursor.fetchall():
    print(l)

# Consultar si el 20 de Julio o esa semana hay feriados
# los feriados se guardan en alguna tabla?
# de db.py sabemos que hay una tabla feriados_previos o similar? no, feriados se cargan de la DB
# miremos las tablas de la DB para ver si hay una tabla de feriados
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tablas = [r[0] for r in cursor.fetchall()]
print("\nTablas en DB:", tablas)

# Si existe tabla feriados o similar, listarla
for t in tablas:
    if 'feriado' in t or 'calendario' in t:
        print(f"\nContenido de tabla {t}:")
        cursor.execute(f"SELECT * FROM {t}")
        for r in cursor.fetchall():
            print(r)

conn.close()
