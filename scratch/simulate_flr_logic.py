import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import datetime
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import rule_engine as _re

servicio_id = 2
fecha_inicio = "2026-07-01"
fecha_fin = "2026-07-31"

fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
fecha_fin_dt = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
offset_dia = fecha_inicio_dt.weekday()

# Feriados
feriados_indices = []
feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin)
for f_str in feriados_db:
    f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < dias:
        feriados_indices.append(delta)
feriados = set(feriados_indices)

# Reglas de servicio y ajustes
reglas_servicio = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas_personal = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas_personal['__servicio__'] = ajustes_servicio

empleados = obtener_empleados(servicio_id, fecha_inicio, dias)
turnos_dict = obtener_turnos(servicio_id)
config_turnos, _, _, _ = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)

# Buscar a BORIA MAYRA
emp = None
for e in empleados:
    if e.nombre == 'BORIA MAYRA':
        emp = e
        break

if not emp:
    print("No se encontró a BORIA MAYRA")
    exit()

print("Empleado:", emp.nombre)
print("Licencias:", emp.dias_licencia)
print("Puestos habilitados:", emp.puestos_habilitados)

# Resolver parámetros
params = _re.resolver_parametros_regla(
    'FINDE_LARGO_REGLAMENTARIO', emp.nombre, fecha_inicio,
    reglas_servicio, emp.reglas, ajustes_reglas_personal
)
params_estricto = _re.resolver_parametros_regla(
    'FINDE_LARGO_REGLAMENTARIO_ESTRICTO', emp.nombre, fecha_inicio,
    reglas_servicio, emp.reglas, ajustes_reglas_personal
)

print("params:", params)
print("params_estricto:", params_estricto)

active = None
if _re.regla_existe(params) and not _re.regla_suspendida(params):
    active = ('normal', params)
elif _re.regla_existe(params_estricto) and not _re.regla_suspendida(params_estricto):
    active = ('estricto', params_estricto)

print("Active:", active)

if active:
    tipo_regla, p = active
    cantidad_req = p.get('cantidad', 1) if isinstance(p, dict) else 1
    
    flr_pref = []
    flr_alt = []

    # Para simular variables de turno, vamos a ver cuáles se crearían en construir_modelo
    turnos_creados = set()
    for dia in range(dias):
        dia_semana = (dia + offset_dia) % 7
        es_finde_o_feriado = (dia_semana >= 5) or (dia in feriados)
        tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
        lista_turnos = config_turnos.get(tipo_dia, {}).keys()
        
        for t in lista_turnos:
            t_info = turnos_dict.get(t)
            puesto_nombre_turno = t_info.puesto_nombre if t_info else None
            
            if puesto_nombre_turno:
                if emp.puestos_habilitados:
                    if puesto_nombre_turno not in emp.puestos_habilitados:
                        continue
                else:
                    if emp.rol and emp.rol != "Rotativo" and emp.rol != puesto_nombre_turno:
                        continue
            turnos_creados.add((emp.nombre, dia, t))

    print(f"Total variables de turno creadas para BORIA MAYRA: {len(turnos_creados)}")

    for d in range(dias):
        dia_sem = (d + offset_dia) % 7
        es_sabado = dia_sem == 5
        es_jueves = dia_sem == 3
        if not (es_sabado or es_jueves):
            continue
        if tipo_regla == 'estricto' and d + 3 >= dias:
            continue

        dias_obj = [d, d + 1, d + 2, d + 3]
        vars_bloque = []
        for d_e in dias_obj:
            if d_e >= dias:
                if tipo_regla == 'estricto':
                    vars_bloque = []
                    break
                continue
            if d_e in emp.dias_licencia:
                vars_bloque = []
                break
            es_f_e = ((d_e + offset_dia) % 7 >= 5) or (d_e in feriados)
            tipo_d = 'Finde_Feriado' if es_f_e else 'Semana'
            for t in config_turnos.get(tipo_d, {}).keys():
                if (emp.nombre, d_e, t) in turnos_creados:
                    vars_bloque.append((emp.nombre, d_e, t))

        if not vars_bloque:
            continue

        if es_sabado:
            flr_pref.append((d, vars_bloque))
        else:
            flr_alt.append((d, vars_bloque))

    print("flr_pref:", [(d, len(vb)) for d, vb in flr_pref])
    print("flr_alt:", [(d, len(vb)) for d, vb in flr_alt])
    print("Total 'todas':", len(flr_pref) + len(flr_alt))
