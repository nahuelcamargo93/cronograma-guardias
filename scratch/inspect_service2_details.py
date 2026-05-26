import sys
import os

sys.path.append(os.getcwd())

import data
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

db_queries.init_licencias()
reglas_servicio = db_queries.cargar_reglas_servicio(2)
ajustes_personal = db_queries.cargar_ajustes_reglas_personal(data.FECHA_INICIO, data.FECHA_FIN)
empleados = obtener_empleados(2, data.FECHA_INICIO, 31)
config_turnos, turnos_dict, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=2, fecha_inicio=data.FECHA_INICIO, fecha_fin=data.FECHA_FIN
)

print("TURNOS CONFIG FOR SERVICE 2:")
for t_name, t_info in turnos_dict.items():
    print(f"  Turno: {t_name:15s} | Horas: {t_info.get('horas')} | Puesto: {t_info.get('puesto_nombre')}")

print("\nDEMANDA REQ FOR SERVICE 2:")
for td, reqs in demanda_req.items():
    print(f"  Tipo Dia: {td}")
    for r in reqs:
        print(f"    Puesto: {r['puesto']:12s} | min: {r['cantidad_min']} | max: {r['cantidad_max']}")

print("\nEMPLOYEES ENABLED SHIFTS:")
for emp in empleados:
    # See what turnos are habilitados
    enabled_turnos = []
    for t_name, t_info in turnos_dict.items():
        if not emp.puestos_habilitados or t_info.get('puesto_nombre') in emp.puestos_habilitados:
            enabled_turnos.append(t_name)
    print(f"  Emp: {emp.nombre:25s} | Habilitados: {enabled_turnos} | Licencias: {len(emp.dias_licencia)}")
