import re

with open(r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\main.py", "r", encoding="utf-8") as f:
    code = f.read()

# Replace db import
code = code.replace("import db as database", "import database.queries as database\nfrom database.data_loader import obtener_empleados, obtener_turnos")

# Update construir_modelo signature
old_sig = "def construir_modelo(df_personal, demanda_turnos, metadata_turnos, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, num_semanas, reglas_personal, ajustes_reglas_personal=None, historial_semana_previa=None, servicio_id=1):"
new_sig = "def construir_modelo(empleados, demanda_turnos, turnos_dict, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, num_semanas, reglas_servicio, ajustes_reglas_personal=None, historial_semana_previa=None, servicio_id=1):"
code = code.replace(old_sig, new_sig)

# Change variables in loop inside construir_modelo
old_loop = """    def dias_en_licencia(nombre):
        \"\"\"Devuelve un set de índices de día (0-based) en que la persona está de LAR o LPP.\"\"\"
        bloqueados = set()
        for licencias in (database.LAR, database.LPP):
            for (lic_ini_str, lic_fin_str) in licencias.get(nombre, []):
                lic_ini = date.fromisoformat(lic_ini_str)
                lic_fin = date.fromisoformat(lic_fin_str)
                for d in range(dias_del_bloque):
                    if lic_ini <= fecha_inicio_dt_d + timedelta(days=d) <= lic_fin:
                        bloqueados.add(d)
        return bloqueados

    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        rol_persona = persona.get('Rol')
        licencia_dias = dias_en_licencia(nombre)"""

new_loop = """    for emp in empleados:
        nombre = emp.nombre
        rol_persona = emp.rol
        licencia_dias = emp.dias_licencia"""
code = code.replace(old_loop, new_loop)

# Change metadata_turnos -> turnos_dict logic
code = code.replace("t_info = metadata_turnos.get(t, {})", "t_info = turnos_dict.get(t)")
code = code.replace("puesto_nombre_turno = t_info.get('puesto_nombre')", "puesto_nombre_turno = t_info.puesto_nombre if t_info else None")

# Replace the resolver_parametros_regla for ASIGNACION_FIJA
code = code.replace("""                params = _re.resolver_parametros_regla(
                    'ASIGNACION_FIJA', nombre, fecha_dia_str,
                    {}, reglas_personal, ajustes_reglas_personal or {}
                )""", """                params = _re.resolver_parametros_regla(
                    'ASIGNACION_FIJA', nombre, fecha_dia_str,
                    reglas_servicio, emp.reglas, ajustes_reglas_personal or {}
                )""")

# Update hard/soft rules calls
old_hard = "aplicar_reglas_duras(modelo, turnos, df_personal, demanda_turnos, metadata_turnos, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, num_semanas, historial_semana_previa=historial_semana_previa, flr_tracker=flr_tracker, servicio_id=servicio_id)"
new_hard = "aplicar_reglas_duras(modelo, turnos, empleados, demanda_turnos, turnos_dict, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, num_semanas, historial_semana_previa, reglas_servicio, ajustes_reglas_personal, servicio_id)"
code = code.replace(old_hard, new_hard)

old_soft = "vars_turno_sem = aplicar_reglas_blandas(modelo, turnos, df_personal, demanda_turnos, dias_del_bloque, feriados, offset_dia, num_semanas, servicio_id=servicio_id, flr_tracker=flr_tracker, historial_semana_previa=historial_semana_previa, metadata_turnos=metadata_turnos)"
new_soft = "vars_turno_sem = aplicar_reglas_blandas(modelo, turnos, empleados, demanda_turnos, turnos_dict, dias_del_bloque, feriados, offset_dia, num_semanas, servicio_id, flr_tracker, historial_semana_previa)"
code = code.replace(old_soft, new_soft)

# Update resolver_modelo definition 
old_res = "def resolver_modelo(modelo, turnos, flr_tracker, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, config_turnos, vars_turno_sem=None):"
new_res = "def resolver_modelo(modelo, turnos, flr_tracker, empleados, dias_del_bloque, feriados, fecha_inicio, offset_dia, config_turnos, vars_turno_sem=None):"
code = code.replace(old_res, new_res)

code = code.replace("for index, persona in df_personal.iterrows():\n                    nombre = persona['Nombre']", "for emp in empleados:\n                    nombre = emp.nombre")

# In main() function
old_main = """    # Cargar configuración de turnos y demanda WFM desde DB
    config_turnos, metadata_turnos, demanda_req, ajustes_db = database.cargar_configuracion_turnos(
        servicio_id=SERVICIO_ID, fecha_inicio=FECHA_INICIO, fecha_fin=FECHA_FIN
    )"""

new_main = """    # Cargar configuración de turnos y demanda WFM desde DB
    config_turnos, metadata_turnos, demanda_req, ajustes_db = database.cargar_configuracion_turnos(
        servicio_id=SERVICIO_ID, fecha_inicio=FECHA_INICIO, fecha_fin=FECHA_FIN
    )
    reglas_servicio_db = database.cargar_reglas_servicio(SERVICIO_ID)
    empleados = obtener_empleados(SERVICIO_ID, FECHA_INICIO, DIAS_DEL_BLOQUE)
    turnos_dict = obtener_turnos(SERVICIO_ID)
    
    # Mantener df_personal porque es usado por reportes (legacy)
    """
code = code.replace(old_main, new_main)

old_call = """    modelo, turnos, flr_tracker, vars_turno_sem = construir_modelo(
        df_personal, config_turnos, metadata_turnos, demanda_req, ajustes_db,
        DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
        reglas_personal=reglas_personal_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=SERVICIO_ID
    )"""

new_call = """    modelo, turnos, flr_tracker, vars_turno_sem = construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=SERVICIO_ID
    )"""
code = code.replace(old_call, new_call)

old_res_call = "df_resultados, flrs_asignados, df_cat_semanas = resolver_modelo(modelo, turnos, flr_tracker, df_personal, DIAS_DEL_BLOQUE, feriados_indices, FECHA_INICIO, offset_dia, config_turnos, vars_turno_sem=vars_turno_sem)"
new_res_call = "df_resultados, flrs_asignados, df_cat_semanas = resolver_modelo(modelo, turnos, flr_tracker, empleados, DIAS_DEL_BLOQUE, feriados_indices, FECHA_INICIO, offset_dia, config_turnos, vars_turno_sem=vars_turno_sem)"
code = code.replace(old_res_call, new_res_call)


with open(r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\main.py", "w", encoding="utf-8") as f:
    f.write(code)

print("main.py refactorizado con éxito")
