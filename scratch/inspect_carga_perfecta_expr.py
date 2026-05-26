import sys
import os
from datetime import date, timedelta

sys.path.append(os.getcwd())

import data
import main
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

# Load data once
db_queries.init_licencias()
config_turnos, metadata_turnos_raw, demanda_req, adjustments = db_queries.cargar_configuracion_turnos(
    servicio_id=data.SERVICIO_ID, fecha_inicio=data.FECHA_INICIO, fecha_fin=data.FECHA_FIN
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(data.SERVICIO_ID)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(data.FECHA_INICIO, data.FECHA_FIN)
empleados = obtener_empleados(data.SERVICIO_ID, data.FECHA_INICIO, 31)
turnos_dict = obtener_turnos(data.SERVICIO_ID)
historial_semana_previa = db_queries.cargar_guardias_previas(data.FECHA_INICIO, dias_atras=28, servicio_id=data.SERVICIO_ID)
offset_dia = 2 # July 1st 2026 is Wednesday
dias_del_bloque = 31

# Build turn variables like main.py does
from ortools.sat.python import cp_model
modelo = cp_model.CpModel()
turnos = {}
fecha_inicio_dt_d = date.fromisoformat(data.FECHA_INICIO)

for emp in empleados:
    nombre = emp.nombre
    rol_persona = emp.rol
    licencia_dias = emp.dias_licencia
    for dia in range(dias_del_bloque):
        dia_semana = (dia + offset_dia) % 7
        es_finde_o_feriado = (dia_semana >= 5) or (dia in [8]) # July 9 is Independence Day holiday
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
                    if rol_persona and rol_persona != "Rotativo" and rol_persona != puesto_nombre_turno:
                        continue
            
            turnos[(nombre, dia, t)] = modelo.NewBoolVar(f'turno_{nombre}_dia{dia}_{t}')

# Now calculate bounds of sum(h_vars_m) + h_lic_m for each employee
meses_en_bloque = {}
for d in range(dias_del_bloque):
    m_key = (fecha_inicio_dt_d + timedelta(days=d)).strftime("%Y-%m")
    meses_en_bloque.setdefault(m_key, []).append(d)

for emp in empleados:
    nombre = emp.nombre
    dias_bloqueados_persona = emp.dias_licencia
    for m_key, dias_m in meses_en_bloque.items():
        h_vars_m_count = 0
        max_possible_hours = 0
        for d in dias_m:
            es_f = ((d + offset_dia) % 7) >= 5 or d in [8]
            tipo_dia_h = "Finde_Feriado" if es_f else "Semana"
            for t in config_turnos.get(tipo_dia_h, {}).keys():
                if (nombre, d, t) in turnos:
                    h_vars_m_count += 1
                    h_t = turnos_dict[t].horas if t in turnos_dict else 6
                    max_possible_hours += h_t
                    
        dias_lic_m = [d for d in dias_m if d in dias_bloqueados_persona]
        val_dia = 144.0 / dias_del_bloque
        h_lic_m = int(val_dia * len(dias_lic_m) + 0.5)
        
        print(f"Emp: {nombre:25s} | Var count: {h_vars_m_count} | max_hours: {max_possible_hours} | h_lic_m: {h_lic_m}")
