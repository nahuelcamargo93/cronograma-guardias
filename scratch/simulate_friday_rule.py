import sqlite3
import datetime
from datetime import date, timedelta
import json

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Load personal
cur.execute("SELECT nombre, servicio_id, activo FROM personal WHERE servicio_id = 3 AND activo = 1")
personal_rows = cur.fetchall()

# We need to load licencias for each personal
licencias_dict = {}
cur.execute("SELECT nombre, fecha_inicio, fecha_fin FROM licencias")
for name, fi, ff in cur.fetchall():
    licencias_dict.setdefault(name, []).append((date.fromisoformat(fi), date.fromisoformat(ff)))

# Load services_reglas
cur.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 3")
servicios_reglas = {row[0]: (json.loads(row[1]), row[2]) for row in cur.fetchall()}

# Load personal_reglas
cur.execute("""
    SELECT pr.personal_nombre, pr.codigo_regla, pr.parametros_json, pr.activo
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 3
""")
personal_reglas = {}
for name, code, params, active in cur.fetchall():
    personal_reglas.setdefault(name, {})[code] = (json.loads(params), active)

# Load personal_reglas_ajustes or similar if they exist
cur.execute("PRAGMA table_info(personal_reglas_ajustes)")
ajustes_cols = [r[1] for r in cur.fetchall()]
ajustes_reglas = {}
if 'personal_nombre' in ajustes_cols:
    cur.execute("SELECT personal_nombre, codigo_regla, suspendida FROM personal_reglas_ajustes")
    for name, code, susp in cur.fetchall():
        ajustes_reglas.setdefault(name, {})[code] = susp

def resolver_parametros_regla(codigo, nombre, fecha_ini_str):
    # check personal specific
    p_reg = personal_reglas.get(nombre, {}).get(codigo)
    if p_reg:
        params, active = p_reg
        if not active:
            return {"suspendida": True}
        return params
    
    # check service rule
    s_reg = servicios_reglas.get(codigo)
    if s_reg:
        params, active = s_reg
        if not active:
            return {"suspendida": True}
        # check if suspended in personal adjustments
        if ajustes_reglas.get(nombre, {}).get(codigo):
            return {"suspendida": True}
        return params
    
    return None

def regla_existe(params):
    return params is not None

def regla_suspendida(params):
    if params is None:
        return True
    return params.get('suspendida', False)

# Set date block details
fecha_inicio_dt = date.fromisoformat("2026-06-01")
fecha_fin_dt = date.fromisoformat("2026-06-30")
dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1
offset_dia = fecha_inicio_dt.weekday()

# Precompute findes
feriados_indices = []
feriados_str = ["2026-06-15", "2026-06-20"]
for f_str in feriados_str:
    f_dt = date.fromisoformat(f_str)
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < dias_del_bloque:
        feriados_indices.append(delta)

findes = {}
for d_f in range(dias_del_bloque):
    fecha_df = fecha_inicio_dt + timedelta(days=d_f)
    dia_semana_f = (d_f + offset_dia) % 7
    es_finde_f = (dia_semana_f >= 5) or (d_f in feriados_indices)
    if es_finde_f:
        lunes_f = (fecha_df - timedelta(days=fecha_df.weekday())).isoformat()
        findes.setdefault(lunes_f, []).append(d_f)

mapa_dias = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6}

print(f"\nSimulation of Friday rules for Service 3 from {fecha_inicio_dt} to {fecha_fin_dt}:")
for row in personal_rows:
    nombre = row[0]
    
    # Calculate dias_licencia
    licencias = licencias_dict.get(nombre, [])
    dias_licencia = set()
    for fi, ff in licencias:
        curr = fi
        while curr <= ff:
            delta = (curr - fecha_inicio_dt).days
            if 0 <= delta < dias_del_bloque:
                dias_licencia.add(delta)
            curr += timedelta(days=1)
            
    params_min = resolver_parametros_regla('MIN_DIA_ESPECIFICO_MES', nombre, fecha_inicio_dt.isoformat())
    params_exacto = resolver_parametros_regla('EXACTO_DIA_ESPECIFICO_MES', nombre, fecha_inicio_dt.isoformat())
    
    has_min = regla_existe(params_min) and not regla_suspendida(params_min)
    has_exacto = regla_existe(params_exacto) and not regla_suspendida(params_exacto)
    
    # Si MIN_DIA_ESPECIFICO_MES está suspendida para este empleado, heredamos la suspensión a EXACTO_DIA_ESPECIFICO_MES
    if has_exacto and params_min is not None and regla_suspendida(params_min):
        has_exacto = False
        
    if not has_min and not has_exacto:
        print(f"{nombre}: NO RULES ACTIVE")
        continue
        
    is_exact = has_exacto
    params = params_exacto if has_exacto else params_min
    
    dia_conf = params.get('dia_semana', 4)
    if isinstance(dia_conf, str):
        dia_str = dia_conf.lower().replace('é', 'e').replace('á', 'a').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        dia_semana_target = mapa_dias.get(dia_str, 4)
    else:
        dia_semana_target = int(dia_conf)
        
    min_dias_req = params.get('exacto_dias', params.get('min_dias', 1))
    
    k = sum(1 for lunes_f, dias_f in findes.items() if any(d_f not in dias_licencia for d_f in dias_f))
    
    if params.get('dinamico_licencias', False):
        if dia_semana_target == 4:
            if k >= 4:
                target_dias = 1
            elif k == 3:
                target_dias = 0
            elif k == 2:
                target_dias = 1
            else:
                target_dias = 0
        else:
            target_dias = min_dias_req
    else:
        target_dias = min_dias_req
        
    # Check what target_dias is
    print(f"Name: {nombre:30s} | has_min: {has_min} | has_exacto: {has_exacto} | is_exact: {is_exact} | k: {k} | target_dias: {target_dias}")

conn.close()
