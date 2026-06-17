import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

print("=== Resumen de Guardias por Fecha en Cronograma 306 ===")
cursor.execute("""
    SELECT fecha, COUNT(*), SUM(horas) 
    FROM guardias 
    WHERE cronograma_id = 306 
    GROUP BY fecha 
    ORDER BY fecha
""")
rows = cursor.fetchall()

feriados_y_findes = ["2026-07-04", "2026-07-05", "2026-07-09", "2026-07-10", "2026-07-11", "2026-07-12", "2026-07-18", "2026-07-19", "2026-07-25", "2026-07-26"]

print("Fecha      | Cantidad Guardias | Total Horas | Tipo Esperado")
print("-" * 60)
for r in rows:
    fecha = r[0]
    tipo = "Finde/Feriado" if fecha in feriados_y_findes or any(f in fecha for f in ["-04", "-05", "-11", "-12", "-18", "-19", "-25", "-26"]) else "Semana"
    # A efectos del test, calculemos el dia de la semana
    import datetime
    dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
    es_finde = dt.weekday() >= 5
    es_feriado = fecha in ["2026-07-09", "2026-07-10"]
    tipo_str = "Feriado" if es_feriado else ("Finde" if es_finde else "Semana")
    print(f"{fecha} | {r[1]:<17} | {r[2]:<11} | {tipo_str}")

print("\n=== Detalle de Guardias en Feriados (9 y 10 de Julio) ===")
cursor.execute("""
    SELECT fecha, turno, nombre, horas 
    FROM guardias 
    WHERE cronograma_id = 306 AND fecha IN ('2026-07-09', '2026-07-10')
    ORDER BY fecha, turno
""")
for r in cursor.fetchall():
    print(r)

print("\n=== Detalle de Guardias en un Fin de Semana (4 y 5 de Julio) ===")
cursor.execute("""
    SELECT fecha, turno, nombre, horas 
    FROM guardias 
    WHERE cronograma_id = 306 AND fecha IN ('2026-07-04', '2026-07-05')
    ORDER BY fecha, turno
""")
for r in cursor.fetchall():
    print(r)

print("\n=== Validación de no existencia de turnos de 6 horas Mañana/Tarde (no especiales) en Fines de Semana y Feriados ===")
cursor.execute("""
    SELECT COUNT(*) 
    FROM guardias 
    WHERE cronograma_id = 306 
      AND (turno LIKE 'Maana%' OR turno LIKE 'Tarde%')
      AND turno NOT LIKE '%especial%'
      AND (
        strftime('%w', fecha) IN ('0', '6') -- Domingo, Sabado
        OR fecha IN ('2026-07-09', '2026-07-10') -- Feriados
      )
""")
count = cursor.fetchone()[0]
print(f"Cantidad de turnos Mañana/Tarde (no especiales) asignados en no-hábiles: {count}")
if count == 0:
    print("¡VALIDACIÓN EXITOSA! Ningún turno de Mañana o Tarde regular fue asignado en fines de semana o feriados.")
else:
    print("¡FALLO EN LA VALIDACIÓN! Se encontraron asignaciones incorrectas.")

conn.close()
