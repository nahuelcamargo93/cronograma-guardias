import sys
sys.path.append('.')
from datetime import date, timedelta
import pandas as pd
from ortools.sat.python import cp_model
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import main
from restricciones.cargador import preparar_assumption, activar_assumptions
import importlib

# Patch cargar_y_ejecutar_todas so construir_modelo doesn't run all rules
main.cargar_y_ejecutar_todas = lambda m, c: None

servicio_id = 2
fecha_inicio = "2026-08-01"
fecha_fin = "2026-08-31"

# Force rule to HARD in DB
import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()
c.execute("""
    UPDATE servicios_reglas 
    SET parametros_json = '{"modo": "HARD", "distancias": {"N": 3, "TN": 3}}', activo = 1
    WHERE servicio_id = 2 AND codigo_regla = 'DISTANCIA_MINIMA_TIPO_SEMANA'
""")
conn.commit()
conn.close()

db_queries.init_licencias(servicio_id)
config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

empleados = obtener_empleados(servicio_id, fecha_inicio, 31)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

fecha_inicio_dt = pd.to_datetime(fecha_inicio)
feriados_indices = [] 
feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
for f in feriados_db:
    f_dt = pd.to_datetime(f)
    diff = (f_dt - fecha_inicio_dt).days
    if 0 <= diff < 31:
        feriados_indices.append(diff)

offset_dia = fecha_inicio_dt.weekday()

status_names = {
    cp_model.OPTIMAL: "OPTIMAL",
    cp_model.FEASIBLE: "FEASIBLE",
    cp_model.INFEASIBLE: "INFEASIBLE",
    cp_model.UNKNOWN: "UNKNOWN"
}

from restricciones.hard import REGLAS_HARD
from restricciones.double import REGLAS_DOUBLE
from restricciones.soft import REGLAS_SOFT

# Build model
modelo, turnos, flr_tracker, ctx = main.construir_modelo(
    empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
    31, feriados_indices, offset_dia, 6,
    reglas_servicio=reglas_servicio_db,
    ajustes_reglas_personal=ajustes_reglas,
    historial_semana_previa=historial_semana_previa,
    servicio_id=servicio_id,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin,
    modo_debug=False,
    force_assumptions=False
)

from restricciones.hard._utils import crear_y_vincular_variables_semanales, determinar_familia_ganadora
crear_y_vincular_variables_semanales(modelo, ctx)

# 1. Apply modified DISTANCIA_MINIMA_TIPO_SEMANA logic
from restricciones.cargador import add_hard

params = ctx.reglas_servicio.get('DISTANCIA_MINIMA_TIPO_SEMANA')
distancias = params.get('distancias', {})
modo = params.get('modo', 'SOFT').upper()
peso_soft = params.get('peso_soft', 10000)

dias_por_semana = {}
for d in range(31):
    fd = date.fromisoformat(fecha_inicio) + timedelta(days=d)
    lunes = fd - timedelta(days=fd.weekday())
    dias_por_semana.setdefault(lunes.isoformat(), []).append(d)
semanas_keys = sorted(dias_por_semana.keys())
primer_lunes = date.fromisoformat(semanas_keys[0])

preparar_assumption(modelo, ctx, 'DISTANCIA_MINIMA_TIPO_SEMANA')

for emp in ctx.empleados:
    nombre = emp.nombre
    nombre_safe = nombre.replace(' ', '_').replace(',', '').replace('-', '_')
    hist_prev = ctx.historial_semana_previa.get(nombre, []) if ctx.historial_semana_previa else []
    
    for fam, d_min in distancias.items():
        d_min = int(d_min)
        w = d_min + 1
        
        # Secuencia historial
        secuencia_hist = []
        for sem_idx in range(w - 1, 0, -1):
            lunes_prev_dt = primer_lunes - timedelta(days=sem_idx * 7)
            ganador_prev = determinar_familia_ganadora(hist_prev, lunes_prev_dt)
            hist_flag = 1 if ganador_prev == fam else 0
            secuencia_hist.append(hist_flag)
            
        # Secuencia variables/constantes de la planificación
        secuencia = list(secuencia_hist)
        for sem_key in semanas_keys:
            # FIX logic: if the week overlaps the past and has guardias in history, treat as constant
            ganador_sem = determinar_familia_ganadora(hist_prev, date.fromisoformat(sem_key))
            if ganador_sem is not None:
                hist_flag = 1 if ganador_sem == fam else 0
                secuencia.append(hist_flag)
            else:
                v_dict = ctx.vars_turno_sem.get((nombre, sem_key))
                if v_dict and fam in v_dict:
                    secuencia.append(v_dict[fam])
                    
        # Apply sliding window constraints
        for i in range(len(secuencia) - w + 1):
            vars_ventana = secuencia[i:i+w]
            if all(isinstance(v, int) for v in vars_ventana):
                continue
                
            constantes = [v for v in vars_ventana if isinstance(v, int)]
            variables = [v for v in vars_ventana if not isinstance(v, int)]
            
            sum_const = sum(constantes)
            rhs = max(0, 1 - sum_const)
            
            if modo == 'HARD':
                add_hard(
                    modelo, ctx,
                    modelo.Add(sum(variables) <= rhs),
                    f"{nombre}_dist_{fam}_w{i}"
                )
            else:
                viol = modelo.NewIntVar(0, len(variables), f"viol_dist_{fam}_{nombre_safe}_w{i}")
                modelo.Add(sum(variables) <= rhs + viol)
                ctx.penalizaciones_soft.append(viol * peso_soft)

# Force DISTANCIA_MINIMA_TIPO_SEMANA
for name, var in ctx.assumptions:
    if name == 'REG_DISTANCIA_MINIMA_TIPO_SEMANA':
        modelo.Add(var == 1)
        break

# Apply baseline
for r_name in REGLAS_HARD:
    modulo = importlib.import_module(r_name)
    codigo = r_name.rsplit('.', 1)[-1].upper()
    ctx.codigo_regla = codigo
    preparar_assumption(modelo, ctx, codigo)
    modulo.apply(modelo, ctx)
    ctx.current_assumption = None

# Apply double
for r_name in REGLAS_DOUBLE:
    if 'distancia_minima_tipo_semana' in r_name: continue
    modulo = importlib.import_module(r_name)
    codigo = r_name.rsplit('.', 1)[-1].upper()
    ctx.codigo_regla = codigo
    preparar_assumption(modelo, ctx, codigo)
    modulo.apply(modelo, ctx)
    ctx.current_assumption = None

# Apply soft
for r_name in REGLAS_SOFT:
    modulo = importlib.import_module(r_name)
    codigo = r_name.rsplit('.', 1)[-1].upper()
    ctx.codigo_regla = codigo
    preparar_assumption(modelo, ctx, codigo)
    modulo.apply(modelo, ctx)
    ctx.current_assumption = None

from restricciones.cargador import construir_objetivo_soft
construir_objetivo_soft(modelo, ctx)

# Force all assumptions to 1
activar_assumptions(modelo, ctx, de_verdad=False)

print("Resolviendo con la regla de distancia corregida...")
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
status = solver.Solve(modelo)
print(f"Resultado con corrección de regla: {status_names.get(status)}")
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("[SUCCESS] ¡El modelo con la regla corregida es VIABLE!")
