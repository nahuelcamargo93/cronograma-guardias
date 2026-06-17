import sqlite3
import pandas as pd
from datetime import date, timedelta

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)

print("=== AUDITORÍA DE NIVELACIÓN HISTÓRICA DE FINES DE SEMANA ===")

# 1. Obtener la configuración actual de MANEJO_FINDES del servicio 1
row_config = conn.execute("""
    SELECT parametros_json FROM servicios_reglas 
    WHERE servicio_id = 1 AND codigo_regla = 'MANEJO_FINDES'
""").fetchone()

if not row_config:
    print("No se encontró la configuración de la regla.")
    conn.close()
    exit()

import json
config = json.loads(row_config[0])
print("Configuración en DB:", config)
por_disp = config.get("por_disponibilidad", {})
niv_conf = config.get("nivelacion_historica", {})

if not niv_conf.get("activo"):
    print("La nivelación histórica no está activa en la configuración actual.")
    conn.close()
    exit()

fecha_inicio_niv = niv_conf.get("fecha_inicio", "2026-07-01")
print(f"Fecha inicio nivelación: {fecha_inicio_niv}")

# 2. Buscar el cronograma recién generado (Julio 2026)
# Buscamos el cronograma más reciente para el Servicio 1 que comience en '2026-07-01'
crono_actual = conn.execute("""
    SELECT id, fecha_inicio, fecha_fin, estado FROM cronogramas
    WHERE fecha_inicio = '2026-07-01'
    ORDER BY id DESC LIMIT 1
""").fetchone()

if not crono_actual:
    print("No se encontró un cronograma generado para Julio de 2026.")
    conn.close()
    exit()

c_id_actual, c_ini_actual, c_fin_actual, estado_actual = crono_actual
print(f"Cronograma actual detectado: ID={c_id_actual}, Rango={c_ini_actual} a {c_fin_actual}, Estado={estado_actual}")

# 3. Calcular Históricos (previos a 2026-07-01, comenzando desde fecha_inicio_niv)
# Para este test, si fecha_inicio_niv es '2026-07-01', el historial previo a esa fecha está vacío,
# o si hay cronogramas anteriores a Julio de 2026 aprobados desde esa fecha.
# Dado que la fecha de inicio es '2026-07-01', la fecha fin de historial es '2026-06-30'.
# Cualquier cronograma aprobado entre '2026-07-01' y '2026-06-30' no existirá, por lo que los históricos serán 0.
# Sin embargo, si quisiéramos auditar el impacto, podemos simular cómo lee la regla y qué asignaciones se hicieron.
# Calculemos las asignaciones de Julio de 2026 del cronograma ID actual.

# Obtener guardias del cronograma actual
df_g = pd.read_sql_query("""
    SELECT g.nombre, g.fecha, g.turno
    FROM guardias g
    WHERE g.cronograma_id = ? AND g.es_finde = 1
""", conn, params=[c_id_actual])

# Calcular fines de semana trabajados en Julio 2026 por empleado
findes_actuales = {}
for idx, row in df_g.iterrows():
    f_dt = date.fromisoformat(row['fecha'])
    wd = f_dt.weekday()
    if wd in (5, 6):
        lunes_str = (f_dt - timedelta(days=wd)).isoformat()
        findes_actuales.setdefault(row['nombre'], {}).setdefault(lunes_str, set()).add(wd)

res_actual = []
for nom, findes_dict in findes_actuales.items():
    comp = sum(1 for wds in findes_dict.values() if len(wds) >= 2)
    med = sum(1 for wds in findes_dict.values() if len(wds) == 1)
    res_actual.append({
        "Empleado": nom,
        "Completos_Julio26": comp,
        "Medios_Julio26": med,
        "Total_FS_Julio26": comp + 0.5 * med
    })

df_res = pd.DataFrame(res_actual)
if df_res.empty:
    print("No se encontraron guardias de fines de semana en el cronograma actual.")
else:
    print("\n=== RESUMEN DE ASIGNACIONES FINES DE SEMANA (JULIO 2026) ===")
    print(df_res.sort_values(by="Total_FS_Julio26", ascending=False).to_string(index=False))

# 4. Mostrar información de personal para verificar roles
df_p = pd.read_sql_query("SELECT nombre, categoria, rol FROM personal WHERE servicio_id = 1 AND activo = 1", conn)
print("\n=== PERSONAL ACTIVO DEL SERVICIO 1 ===")
print(df_p.to_string(index=False))

conn.close()
