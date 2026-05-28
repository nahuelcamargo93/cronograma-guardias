"""
Verificar si algún médico tiene ASIGNACION_FIJA en viernes
que pueda generar conflicto con EXACTO_DIA_ESPECIFICO_MES_HARD
"""
import sys, os
sys.path.append(os.path.abspath('.'))
from database import queries as db_queries
from database.data_loader import obtener_empleados
import rule_engine as _re
from datetime import date, timedelta

FECHA_INICIO = '2026-06-01'
SERVICIO_ID = 3
db_queries.init_licencias()
reglas_servicio = db_queries.cargar_reglas_servicio(SERVICIO_ID)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(FECHA_INICIO, '2026-06-30')
empleados = obtener_empleados(SERVICIO_ID, FECHA_INICIO, 30)
fecha_ini = date.fromisoformat(FECHA_INICIO)

# Viernes del mes
viernes = [(d, (fecha_ini + timedelta(days=d)).isoformat()) 
           for d in range(30) 
           if (fecha_ini + timedelta(days=d)).weekday() == 4]

print(f"Viernes de junio: {[v[1] for v in viernes]}")
print()

print("=== ASIGNACION_FIJA en viernes ===")
for emp in empleados:
    for d, fecha_str in viernes:
        p = _re.resolver_parametros_regla('ASIGNACION_FIJA', emp.nombre, fecha_str, reglas_servicio, emp.reglas, ajustes_reglas)
        if _re.regla_existe(p) and not _re.regla_suspendida(p):
            print(f"  {emp.nombre}: {fecha_str} => {p}")

print()
print("=== Chequeo: doble constraint (hard + soft) para la misma persona ===")
print("La regla SOFT crea: sum(vars_dia) + viol_under - viol_over == 1")
print("La regla HARD crea: sum(vars_dia) == 1")
print("Esto deberia ser compatible (viol_under=0, viol_over=0)")
print()
print("=== PERO: ¿Qué pasa con ASIGNACION_FIJA en un viernes + hard? ===")
print("Si un empleado tiene ASIGNACION_FIJA en un viernes X (lo obliga a trabajar ese viernes)")
print("y la regla hard dice 'exactamente 1 viernes', el solver debe asignar exactamente ese viernes.")
print("Eso por sí solo no es un problema. PERO si tiene descanso de 48hs del jueves 4...")
print()

# Verificar descanso: si alguien trabaja el jueves, ¿puede trabajar el viernes?
print("=== Turnos que duran 48hs (G) ===")
db_queries_conn = db_queries.sqlite3.connect('cronograma_inteligente.db')
cur = db_queries_conn.cursor()
cur.execute("SELECT nombre, horas FROM turnos_config WHERE servicio_id = 3")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}hs")
db_queries_conn.close()
