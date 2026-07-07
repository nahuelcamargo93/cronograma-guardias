import sys
sys.path.insert(0, '.')
import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model
from database import schema as db_schema
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import restricciones.hard._utils as hard_utils
import copy

# Redefinir la función con assumptions
def crear_y_vincular_variables_semanales_with_assumptions(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    dias_por_semana = {}
    for d in range(ctx.dias):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        lunes = fecha_d - timedelta(days=fecha_d.weekday())
        dias_por_semana.setdefault(lunes.isoformat(), []).append(d)

    for emp in ctx.empleados:
        nombre = emp.nombre
        hist_prev = ctx.historial_semana_previa.get(nombre, []) if ctx.historial_semana_previa else []
        for sem_key, dias_sem in dias_por_semana.items():
            sid = sem_key.replace("-", "_")
            lunes_dt = date.fromisoformat(sem_key)
            is_M  = modelo.NewBoolVar(f'is_M_{nombre}_{sid}')
            is_T  = modelo.NewBoolVar(f'is_T_{nombre}_{sid}')
            is_TN = modelo.NewBoolVar(f'is_TN_{nombre}_{sid}')
            is_N  = modelo.NewBoolVar(f'is_N_{nombre}_{sid}')
            ctx.vars_turno_sem[(nombre, sem_key)] = {'M': is_M, 'T': is_T, 'TN': is_TN, 'N': is_N}

            for d in dias_sem:
                for key, var in [('M', is_M), ('T', is_T), ('TN', is_TN), ('N', is_N)]:
                    if (nombre, d, key) in ctx.turnos:
                        # Implicación
                        b = modelo.NewBoolVar(f"impl_{nombre}_{d}_{key}")
                        modelo.AddImplication(ctx.turnos[(nombre, d, key)], var).OnlyEnforceIf(b)
                        ctx.assumptions.append((f"impl_{nombre}_d{d}_{key}", b))
                
                if (nombre, d, 'MT') in ctx.turnos:
                    b = modelo.NewBoolVar(f"impl_MT_{nombre}_{d}")
                    modelo.Add(is_M + is_T >= 1).OnlyEnforceIf([ctx.turnos[(nombre, d, 'MT')], b])
                    ctx.assumptions.append((f"impl_MT_{nombre}_d{d}", b))
                if (nombre, d, 'TNN') in ctx.turnos:
                    b = modelo.NewBoolVar(f"impl_TNN_{nombre}_{d}")
                    modelo.Add(is_TN + is_N >= 1).OnlyEnforceIf([ctx.turnos[(nombre, d, 'TNN')], b])
                    ctx.assumptions.append((f"impl_TNN_{nombre}_d{d}", b))

            ganador = hard_utils.determinar_familia_ganadora(hist_prev, lunes_dt)
            hist_flags = {'M': 0, 'T': 0, 'TN': 0, 'N': 0}
            if ganador:
                hist_flags[ganador] = 1
                var_map = {'M': is_M, 'T': is_T, 'TN': is_TN, 'N': is_N}
                # Ganador de la semana fijado
                b = modelo.NewBoolVar(f"ganador_{nombre}_{sid}")
                modelo.Add(var_map[ganador] == 1).OnlyEnforceIf(b)
                ctx.assumptions.append((f"ganador_{nombre}_{sid}_{ganador}", b))
                
            vars_M  = [ctx.turnos[(nombre, d, 'M')]  for d in dias_sem if (nombre, d, 'M')  in ctx.turnos]
            vars_T  = [ctx.turnos[(nombre, d, 'T')]  for d in dias_sem if (nombre, d, 'T')  in ctx.turnos]
            vars_TN = [ctx.turnos[(nombre, d, 'TN')] for d in dias_sem if (nombre, d, 'TN') in ctx.turnos]
            vars_N  = [ctx.turnos[(nombre, d, 'N')]  for d in dias_sem if (nombre, d, 'N')  in ctx.turnos]
            vars_MT  = [ctx.turnos[(nombre, d, 'MT')]  for d in dias_sem if (nombre, d, 'MT')  in ctx.turnos]
            vars_TNN = [ctx.turnos[(nombre, d, 'TNN')] for d in dias_sem if (nombre, d, 'TNN') in ctx.turnos]
            
            b_M = modelo.NewBoolVar(f"vinc_M_{nombre}_{sid}")
            modelo.Add(is_M  <= sum(vars_M)  + sum(vars_MT)  + hist_flags['M']).OnlyEnforceIf(b_M)
            ctx.assumptions.append((f"vinc_M_{nombre}_{sid}", b_M))
            
            b_T = modelo.NewBoolVar(f"vinc_T_{nombre}_{sid}")
            modelo.Add(is_T  <= sum(vars_T)  + sum(vars_MT)  + hist_flags['T']).OnlyEnforceIf(b_T)
            ctx.assumptions.append((f"vinc_T_{nombre}_{sid}", b_T))
            
            b_TN = modelo.NewBoolVar(f"vinc_TN_{nombre}_{sid}")
            modelo.Add(is_TN <= sum(vars_TN) + sum(vars_TNN) + hist_flags['TN']).OnlyEnforceIf(b_TN)
            ctx.assumptions.append((f"vinc_TN_{nombre}_{sid}", b_TN))
            
            b_N = modelo.NewBoolVar(f"vinc_N_{nombre}_{sid}")
            modelo.Add(is_N  <= sum(vars_N)  + sum(vars_TNN) + hist_flags['N']).OnlyEnforceIf(b_N)
            ctx.assumptions.append((f"vinc_N_{nombre}_{sid}", b_N))

# Monkey patch
hard_utils.crear_y_vincular_variables_semanales = crear_y_vincular_variables_semanales_with_assumptions

# Importar construir_modelo después del patch
from main import construir_modelo

db_schema.inicializar_db()
servicio_id = 2
fecha_inicio = "2026-08-01"
fecha_fin = "2026-08-31"

fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
DIAS_DEL_BLOQUE = total_dias

# Calcular semanas
lunes_unicos = set()
for d in range(DIAS_DEL_BLOQUE):
    fecha_d = fecha_inicio_dt + datetime.timedelta(days=d)
    lunes = fecha_d - datetime.timedelta(days=fecha_d.weekday())
    lunes_unicos.add(lunes.date())
num_semanas = len(lunes_unicos)

feriados_indices = []
feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
for f_str in feriados_db:
    f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < DIAS_DEL_BLOQUE:
        feriados_indices.append(delta)

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

empleados = obtener_empleados(servicio_id, fecha_inicio, DIAS_DEL_BLOQUE)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
offset_dia = fecha_inicio_dt.weekday()

# Reglas duras conocidas para excluir
codigos_reglas = [
    'COBERTURA_DINAMICA',
    'DESCANSO_ENTRE_TURNOS',
    'ESQUEMA_SEMANAL_ENFERMERIA',
    'EXCLUIR_TURNOS',
    'FINDE_POST_LICENCIA',
    'FIN_LICENCIA',
    'MANEJO_FINDES',
    'MAX_DIAS_CONTINUOS',
    'MAX_FERIADOS_ANUAL',
    'MAX_HORAS_SEMANA',
    'MEZCLA_SEMANAL_DURA',
    'NO_REPETIR_TURNO_CONSECUTIVO',
    'DISTANCIA_MINIMA_TIPO_SEMANA',
    'TURNO_PREVIO_LICENCIA',
    'UN_TURNO_POR_DIA'
]

# Simular Etapa B: sin individuales, sin reglas globales hard, sin licencias, sin ajustes
empleados_clon = []
for emp in empleados:
    e_copy = copy.copy(emp)
    e_copy.dias_licencia = set() # sin licencias
    e_copy.reglas = {} # sin reglas individuales
    empleados_clon.append(e_copy)

ajustes_reglas_clon = {} # sin ajustes de reglas

exclusiones_dict = set()
for cod in codigos_reglas:
    exclusiones_dict.add((cod, None))

modelo_t, turnos_t, flr_t, ctx_t = construir_modelo(
    empleados_clon, config_turnos, turnos_dict, demanda_req, ajustes_db,
    DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
    reglas_servicio=reglas_servicio_db,
    ajustes_reglas_personal=ajustes_reglas_clon,
    historial_semana_previa=historial_semana_previa,
    servicio_id=servicio_id,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin,
    modo_debug=False,
    force_assumptions=True,
    modo_debug_hard=False,
    exclusiones=exclusiones_dict
)

# Activar assumptions para el solver
from restricciones.cargador import activar_assumptions
activar_assumptions(modelo_t, ctx_t, de_verdad=True)

solver_t = cp_model.CpSolver()
solver_t.parameters.max_time_in_seconds = 10
status_t = solver_t.Solve(modelo_t)
print(f"Estado del solver en el sub-modelo: {solver_t.StatusName(status_t)}")

if status_t == cp_model.INFEASIBLE:
    print("Sufficient assumptions for infeasibility:")
    assumptions_inf = solver_t.SufficientAssumptionsForInfeasibility()
    assumptions_map = {b.Index(): name for name, b in ctx_t.assumptions}
    for idx in assumptions_inf:
        print(f" - {assumptions_map.get(idx, f'Var {idx}')}")
