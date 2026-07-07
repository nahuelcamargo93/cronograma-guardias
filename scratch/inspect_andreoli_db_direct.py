import sqlite3
import pandas as pd
from datetime import date, timedelta

conn = sqlite3.connect("cronograma_inteligente.db")

# Obtener guardias de Andreoli Luciana
df_g = pd.read_sql_query("""
    SELECT fecha, turno, horas 
    FROM guardias 
    WHERE cronograma_id = 589 AND nombre = 'ANDREOLI LUCIANA'
    ORDER BY fecha
""", conn)

print("=== Guardias de ANDREOLI LUCIANA ===")
print(df_g)

# Evaluar fines de semana de agosto de 2026
fecha_inicio_dt = date(2026, 8, 1)
dias_del_bloque = 31

# Fines de semana
findes = [
    ("2026-08-01", "2026-08-02"),
    ("2026-08-08", "2026-08-09"),
    ("2026-08-15", "2026-08-16"),
    ("2026-08-22", "2026-08-23"),
    ("2026-08-29", "2026-08-30")
]

guardias_fechas = set(df_g['fecha'].tolist())

print("\n=== Estado de Fines de Semana ===")
completos_trabajados = 0
medios_trabajados = 0
libres = 0

for sat, sun in findes:
    sat_tr = sat in guardias_fechas
    sun_tr = sun in guardias_fechas
    if sat_tr and sun_tr:
        status = "COMPLETO TRABAJADO"
        completos_trabajados += 1
    elif sat_tr or sun_tr:
        status = "MEDIO TRABAJADO"
        medios_trabajados += 1
    else:
        status = "LIBRE"
        libres += 1
    print(f"  Finde {sat} / {sun}: {status}")

print(f"\nResumen: Completos={completos_trabajados}, Medios={medios_trabajados}, Libres={libres}")

# Verificar si tiene algún bloque de 4 días libres consecutivos
dias_trabajados = [0] * 31
for d in range(31):
    fecha_str = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m-%d")
    if fecha_str in guardias_fechas:
        dias_trabajados[d] = 1

print("\n=== Dias Trabajados (0=Libre, 1=Trabajado) ===")
print(dias_trabajados)

# Buscar bloques de 4 libres
for d in range(31 - 3):
    if sum(dias_trabajados[d:d+4]) == 0:
        fi = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m-%d")
        ff = (fecha_inicio_dt + timedelta(days=d+3)).strftime("%Y-%m-%d")
        print(f"  Encontrado bloque de 4 libres: {fi} a {ff} (d={d})")

conn.close()
