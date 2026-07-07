import sys, os
sys.path.append(os.getcwd())

import sqlite3
import pandas as pd
from datetime import date, timedelta
import rule_engine as _re
import database.queries as q
from database.data_loader import obtener_empleados, obtener_turnos

servicio_id = 1
fecha_inicio = "2026-08-01"
dias_del_bloque = 31

df = pd.DataFrame(q.obtener_personal_db(servicio_id))
df = q.cargar_datos_personales_bd(df)
reglas_servicio = q.cargar_reglas_servicio(servicio_id)
ajustes_reglas_personal = q.cargar_ajustes_reglas_personal(fecha_inicio, "2026-08-31")

empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
turnos_dict = obtener_turnos(servicio_id)
config_oferta, turnos_info, demanda_req, ajustes_db = q.cargar_configuracion_turnos(servicio_id)
fecha_inicio_dt = date.fromisoformat(fecha_inicio)
offset_dia = fecha_inicio_dt.weekday()

emp = next(e for e in empleados if e.nombre == 'Camargo, Nahuel')

print(f"=== FLR DIAGNOSIS FOR {emp.nombre} ===")
params = _re.resolver_parametros_regla(
    'FINDE_LARGO_REGLAMENTARIO', emp.nombre, fecha_inicio,
    reglas_servicio, emp.reglas, ajustes_reglas_personal
)
print("Rule Params:", params)

# 1. Agrupar findes por semana
findes = {}
for d in range(dias_del_bloque):
    wd = (fecha_inicio_dt + timedelta(days=d)).weekday()
    if wd in (5, 6):
        fd = fecha_inicio_dt + timedelta(days=d)
        lunes = (fd - timedelta(days=wd)).isoformat()
        findes.setdefault(lunes, []).append(d)

# 2. Calcular disponibilidad (fines de semana donde al menos un día no está en licencias)
k = sum(1 for _, dias in findes.items() if any(d not in emp.dias_licencia for d in dias))
print("Available weekends (k):", k)

# 3. Determinar cantidad requerida basada en por_disponibilidad
pd = params.get('por_disponibilidad')
cantidad_req = pd.get(str(k), pd.get(k, 0)) if isinstance(pd, dict) else (1 if k >= 3 else 0)
print("Required FLRs:", cantidad_req)

flr_permitidos = params.get('flr_permitidos', ["jd", "sm"])
allowed_wds = []
wd_map = {"jd": 3, "vl": 4, "sm": 5}
for pref in flr_permitidos:
    if pref in wd_map:
        allowed_wds.append((wd_map[pref], pref))
print("Allowed wds:", allowed_wds)

# Simular construcción de variables de turno para Camargo
turnos_keys = set()
for d in range(dias_del_bloque):
    dia_semana = (d + offset_dia) % 7
    es_finde_o_feriado = (dia_semana >= 5) or (d in []) # no feriados for simplicity
    tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
    lista_turnos = config_turnos = config_oferta.get(tipo_dia, {}).keys()
    
    for t in lista_turnos:
        t_config = config_oferta.get(tipo_dia, {}).get(t, {})
        dias_hab_str = t_config.get("Dias_Habilitados", "0,1,2,3,4,5,6")
        dias_permitidos = {int(x) for x in dias_hab_str.split(",") if x.strip().isdigit()}
        
        if es_finde_o_feriado:
            if not (5 in dias_permitidos or 6 in dias_permitidos): continue
        else:
            if dia_semana not in dias_permitidos: continue
            
        t_info = turnos_dict.get(t)
        puesto_nombre_turno = t_info.puesto_nombre if t_info else None
        if puesto_nombre_turno and puesto_nombre_turno not in emp.puestos_habilitados:
            continue
            
        turnos_keys.add((emp.nombre, d, t))

print("Total turnos_keys created:", len(turnos_keys))
print("Sample turnos_keys:", list(turnos_keys)[:10])

print("\n--- Analizando cada día d como candidato FLR ---")
for d in range(dias_del_bloque):
    dia_sem = (d + offset_dia) % 7
    pref_activo = next((pref for wd, pref in allowed_wds if wd == dia_sem), None)
    if not pref_activo:
        continue
    
    dias_obj = [d, d + 1, d + 2, d + 3]
    vars_bloque = []
    for d_e in dias_obj:
        if d_e >= dias_del_bloque:
            continue
        if d_e in emp.dias_licencia:
            vars_bloque = []
            break
        es_f_e = ((d_e + offset_dia) % 7 >= 5) # no feriados
        tipo_d = 'Finde_Feriado' if es_f_e else 'Semana'
        for t in config_oferta.get(tipo_d, {}).keys():
            if (emp.nombre, d_e, t) in turnos_keys:
                vars_bloque.append(t)
                
    print(f"Dia d={d} (weekday={dia_sem}, pref={pref_activo}):")
    print(f"  dias_obj: {dias_obj}")
    print(f"  turnos del bloque (vars_bloque): {vars_bloque}")
    
    if not vars_bloque:
        print("  --> EXCLUIDO: no tiene variables de turno en el bloque.")
        continue
        
    # Verificar adyacencia
    # Anterior
    d_prev = d - 1
    if d_prev >= 0:
        es_f_p = ((d_prev + offset_dia) % 7 >= 5)
        vars_prev = [t for t in config_oferta.get('Finde_Feriado' if es_f_p else 'Semana', {}).keys() if (emp.nombre, d_prev, t) in turnos_keys]
        print(f"  vars_prev (dia {d_prev}): {vars_prev}")
    else:
        print(f"  vars_prev (dia {d_prev}): FUERA DE RANGO")
        
    # Posterior
    d_post = d + 4
    if d_post < dias_del_bloque:
        es_f_po = ((d_post + offset_dia) % 7 >= 5)
        vars_post = [t for t in config_oferta.get('Finde_Feriado' if es_f_po else 'Semana', {}).keys() if (emp.nombre, d_post, t) in turnos_keys]
        print(f"  vars_post (dia {d_post}): {vars_post}")
    else:
        print(f"  vars_post (dia {d_post}): FUERA DE RANGO")
