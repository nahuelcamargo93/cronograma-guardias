import main
from database import queries as q
from database.data_loader import obtener_empleados, obtener_turnos
from ortools.sat.python import cp_model
from datetime import date
import copy

servicio_id = 2
fecha_inicio = "2026-08-01"
dias_del_bloque = 31

print("Cargando personal...")
empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
# Borrar licencias
for emp in empleados:
    emp.dias_licencia = set()
    emp.tipos_licencia = {}

# Cargar configuración turnos
turnos_dict = obtener_turnos(servicio_id)
config_turnos, _, demanda_req, ajustes_db = q.cargar_configuracion_turnos(servicio_id, fecha_inicio, None)

# Cargar historial real
historial_semana_previa = q.cargar_guardias_previas(fecha_inicio, servicio_id=servicio_id)

# Cargar reglas de servicio reales
reglas_servicio_base = q.cargar_reglas_servicio(servicio_id)

feriados_indices = set()
offset_dia = date.fromisoformat(fecha_inicio).weekday()
num_semanas = 5

reglas_a_probar = [
    'MANEJO_FINDES',
    'MIN_TURNOS_SEMANA',
    'MIN_FRANCOS_SEMANA',
    'MAX_DIAS_CONTINUOS',
    'MAX_FRANCOS_SEMANA',
    'MAX_FRANCOS_CONTINUOS',
    'NO_REPETIR_TURNO_CONSECUTIVO',
    'BRECHA_DIARIA_PERSONAL'
]

for reg in reglas_a_probar:
    if reg not in reglas_servicio_base:
        continue
        
    print(f"\n>>> Probando desactivando únicamente la regla: {reg}...")
    reglas_servicio = copy.deepcopy(reglas_servicio_base)
    reglas_servicio.pop(reg)  # Remover regla
    
    modelo, turnos, flr, ctx = main.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        dias_del_bloque, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio,
        ajustes_reglas_personal={},
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin="2026-08-31",
        modo_debug=False,
        force_assumptions=False
    )
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 3  # Rápido para presolve
    status = solver.Solve(modelo)
    status_name = solver.StatusName(status)
    print(f"Resultado al desactivar {reg}: {status_name}")
    if status_name != "INFEASIBLE":
        print(f"!!! LA REGLA CULPABLE DE LA INFACTIBILIDAD ES: {reg}")
        break

print("\nDiagnóstico secuencial terminado.")
