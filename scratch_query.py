import sys
sys.path.append('.')
from datetime import date
import pandas as pd
from ortools.sat.python import cp_model
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo
import importlib

servicio_id = 2
fecha_inicio = "2026-08-01"
fecha_fin = "2026-08-31"

# Cargar configuraciones
db_queries.init_licencias(servicio_id) # Cargar licencias correctamente!
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

# Crear modelo de forma similar a construir_modelo pero paso a paso
from main import ContextoModelo
modelo = cp_model.CpModel()
flr_tracker = {}
turnos = {}

# Definir variables
for emp in empleados:
    nombre = emp.nombre
    rol_persona = emp.rol
    for dia in range(31):
        dia_semana = (dia + offset_dia) % 7
        es_finde_o_feriado = (dia_semana >= 5) or (dia in feriados_indices)
        tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
        lista_turnos = config_turnos.get(tipo_dia, {}).keys()
        for t in lista_turnos:
            t_config = config_turnos.get(tipo_dia, {}).get(t, {})
            dias_hab_str = t_config.get("Dias_Habilitados", "0,1,2,3,4,5,6")
            dias_permitidos = {int(x) for x in dias_hab_str.split(",") if x.strip().isdigit()}
            if es_finde_o_feriado:
                if not (5 in dias_permitidos or 6 in dias_permitidos): continue
            else:
                if dia_semana not in dias_permitidos: continue
            t_info = turnos_dict.get(t)
            puesto_nombre_turno = t_info.puesto_nombre if t_info else None
            if puesto_nombre_turno:
                if emp.puestos_habilitados:
                    if puesto_nombre_turno not in emp.puestos_habilitados: continue
                else:
                    if rol_persona and rol_persona != "Rotativo" and rol_persona != puesto_nombre_turno: continue
            turnos[(nombre, dia, t)] = modelo.NewBoolVar(f'turno_{nombre}_dia{dia}_{t}')

ctx = ContextoModelo(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
    dias=31, num_semanas=5, offset_dia=offset_dia, feriados=set(feriados_indices),
    turnos=turnos, empleados=empleados, traductor=None, turnos_dict=turnos_dict,
    demanda_turnos=config_turnos, demanda_req=demanda_req, ajustes_demanda=ajustes_db,
    reglas_servicio=reglas_servicio_db, ajustes_reglas_personal=ajustes_reglas,
    historial_semana_previa=historial_semana_previa, flr_tracker=flr_tracker,
    modo_debug=True, modo_debug_hard=False, exclusiones=set(), dias_bloqueados=set()
)

print(f"Despues de variables: {len(modelo.Proto().constraints)} restricciones")

def print_suspicious_constraints(msg):
    count = 0
    for idx, c in enumerate(modelo.Proto().constraints):
        if not c.enforcement_literal:
            desc = str(c).strip().replace('\n', ' ')
            if "is_" in desc or "viol_" in desc or "excl_" in desc:
                continue
            # Mostrar las que fuerzan variables a 0
            if "coeffs: 1" in desc and "domain: 0" in desc and desc.count("domain: 0") >= 2:
                count += 1
                if count <= 5:
                    # Mapear nombres
                    import re
                    desc_with_names = desc
                    matches = re.finditer(r'vars:\s*(\d+)', desc)
                    for m in matches:
                        v_idx = int(m.group(1))
                        v_name = modelo.Proto().variables[v_idx].name
                        desc_with_names = desc_with_names.replace(m.group(0), f"var({v_name})")
                    print(f"  Strict zero constraint: {desc_with_names}")
    print(f"{msg}: {count} strict zero constraints")

# 1. Vincular variables semanales
from restricciones.hard._utils import crear_y_vincular_variables_semanales
crear_y_vincular_variables_semanales(modelo, ctx)
print_suspicious_constraints("Despues de crear_y_vincular_variables_semanales")

# 2. Ejecutar reglas hard una por una
from restricciones.hard import REGLAS_HARD
from restricciones.cargador import preparar_assumption

for r_name in REGLAS_HARD:
    modulo = importlib.import_module(r_name)
    codigo = r_name.rsplit('.', 1)[-1].upper()
    ctx.codigo_regla = codigo
    preparar_assumption(modelo, ctx, codigo)
    modulo.apply(modelo, ctx)
    ctx.current_assumption = None
    print_suspicious_constraints(f"Despues de regla {codigo}")

# 3. Ejecutar reglas double
from restricciones.double import REGLAS_DOUBLE
for r_name in REGLAS_DOUBLE:
    modulo = importlib.import_module(r_name)
    codigo = r_name.rsplit('.', 1)[-1].upper()
    ctx.codigo_regla = codigo
    preparar_assumption(modelo, ctx, codigo)
    modulo.apply(modelo, ctx)
    ctx.current_assumption = None
    print_suspicious_constraints(f"Despues de regla double {codigo}")
