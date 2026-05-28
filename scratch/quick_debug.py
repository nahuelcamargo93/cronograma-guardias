"""
Diagnóstico rápido: prueba cada regla desactivada para aislar el culpable.
Timeout muy corto (5s) por iteración para ir rápido.
"""
import sys, datetime
sys.path.insert(0, '.')

from data import FECHA_INICIO, FECHA_FIN, FERIADOS, SERVICIO_ID
from database import queries as db_queries, schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
from ortools.sat.python import cp_model
from debug_imposibilidad import construir_modelo_test

db_schema.inicializar_db()
db_queries.init_licencias()

fecha_inicio = FECHA_INICIO
fecha_fin = FECHA_FIN
fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
fecha_fin_dt = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
num_semanas = (total_dias + 6) // 7

feriados_indices = []
for f_str in FERIADOS:
    f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < total_dias:
        feriados_indices.append(delta)

config_turnos, _, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=SERVICIO_ID, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(SERVICIO_ID)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, SERVICIO_ID)
ajustes_reglas['__servicio__'] = ajustes_servicio

empleados = obtener_empleados(SERVICIO_ID, fecha_inicio, total_dias)
turnos_dict = obtener_turnos(SERVICIO_ID)
historial = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=SERVICIO_ID)
offset_dia = fecha_inicio_dt.weekday()

args = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias,
        feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas,
        historial, SERVICIO_ID)

def probar(reglas_ignorar, timeout=5):
    modelo = construir_modelo_test(*args, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
                                   reglas_a_ignorar=reglas_ignorar)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout
    solver.parameters.log_search_progress = False
    status = solver.Solve(modelo)
    return status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

print("Diagnosticando... (cada test = 5s max)")
print()

# Lista completa de reglas duras
reglas = [
    'ASIGNACION_FIJA', 'LICENCIAS', 'FRANCO_FORZADO', 'MAX_TURNOS', 'EXCLUIR_TURNOS',
    'MIN_TURNOS', 'COBERTURA_DINAMICA', 'LIMITE_HORAS_SEMANALES', 'DESCANSO_ENTRE_TURNOS',
    'MIN_FINDES_MES', 'EXACTO_FINDE_Y_DIA', 'UN_SOLO_TURNO_POR_DIA',
    'MAX_HORAS_MES_CALENDARIO', 'MIN_HORAS_MES_CALENDARIO',
    'REGLAS_BLANDAS'
]

culpables = []
for regla in reglas:
    ok = probar([regla])
    estado = "FACTIBLE si se desactiva" if ok else "no resuelve"
    print(f"  {'[WARN]' if ok else '[ OK ]'} {regla}: {estado}")
    if ok:
        culpables.append(regla)

print()
if culpables:
    print(f"Reglas que al desactivarse hacen el modelo factible: {culpables}")
    # Probar pares de las no-culpables mas importantes
    no_culpables = [r for r in ['COBERTURA_DINAMICA', 'DESCANSO_ENTRE_TURNOS', 'EXACTO_FINDE_Y_DIA', 'MIN_HORAS_MES_CALENDARIO'] if r not in culpables]
    if len(no_culpables) >= 2:
        print("\nProbando pares de reglas clave:")
        for i in range(len(no_culpables)):
            for j in range(i+1, len(no_culpables)):
                par = [no_culpables[i], no_culpables[j]]
                ok = probar(par)
                if ok:
                    print(f"  [WARN] Desactivar {par} -> FACTIBLE")
else:
    print("Ninguna regla individual resuelve el problema - es combinacion")
    # Probar pares
    combos = [
        ['COBERTURA_DINAMICA', 'DESCANSO_ENTRE_TURNOS'],
        ['COBERTURA_DINAMICA', 'MIN_HORAS_MES_CALENDARIO'],
        ['COBERTURA_DINAMICA', 'EXACTO_FINDE_Y_DIA'],
        ['DESCANSO_ENTRE_TURNOS', 'MIN_HORAS_MES_CALENDARIO'],
        ['DESCANSO_ENTRE_TURNOS', 'EXACTO_FINDE_Y_DIA'],
        ['MIN_HORAS_MES_CALENDARIO', 'EXACTO_FINDE_Y_DIA'],
        ['COBERTURA_DINAMICA', 'MAX_HORAS_MES_CALENDARIO'],
    ]
    print("\nProbando pares:")
    for par in combos:
        ok = probar(par)
        if ok:
            print(f"  [WARN] Desactivar {par} -> FACTIBLE")
        else:
            print(f"  [ OK ] Desactivar {par} -> aun inviable")
