import sqlite3
import pandas as pd
import datetime
from datetime import date, timedelta

from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import rule_engine as _re

servicio_id = 2
fecha_inicio = "2026-08-01"
fecha_fin = "2026-08-31"

fecha_inicio_dt = date.fromisoformat(fecha_inicio)
fecha_fin_dt = date.fromisoformat(fecha_fin)
dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1

lunes_unicos = set()
for d in range(dias_del_bloque):
    fecha_d = fecha_inicio_dt + timedelta(days=d)
    lunes = fecha_d - timedelta(days=fecha_d.weekday())
    lunes_unicos.add(lunes)
num_semanas = len(lunes_unicos)

feriados_indices = []
feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
for f_str in feriados_db:
    f_dt = date.fromisoformat(f_str)
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < dias_del_bloque:
        feriados_indices.append(delta)

config_turnos, turnos_info, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)

findes_raw = {}
for d in range(dias_del_bloque):
    wd = (fecha_inicio_dt + timedelta(days=d)).weekday()
    if wd in (5, 6):
        fd = fecha_inicio_dt + timedelta(days=d)
        lunes = (fd - timedelta(days=wd)).isoformat()
        findes_raw.setdefault(lunes, []).append((d, wd))

findes = {
    lunes: dias_f for lunes, dias_f in findes_raw.items()
    if any(w == 5 for _, w in dias_f) and any(w == 6 for _, w in dias_f)
}

print("=== Targets de FLR para todos los empleados ===")
for emp in empleados:
    # Calcular disponibilidad
    def es_finde_previo_lpp(emp, d_idx, fecha_inicio_dt) -> bool:
        fecha_d = fecha_inicio_dt + timedelta(days=d_idx)
        wd = fecha_d.weekday()
        if wd not in (5, 6):
            return False
        lunes_idx = d_idx + (2 if wd == 5 else 1)
        if lunes_idx in emp.dias_licencia:
            tipos_lic = getattr(emp, 'tipos_licencia', {})
            if tipos_lic.get(lunes_idx) == 'LPP':
                if lunes_idx == 0 or (lunes_idx - 1) not in emp.dias_licencia:
                    return True
        return False

    def _disponible(d_idx):
        if d_idx in emp.dias_licencia:
            return False
        if es_finde_previo_lpp(emp, d_idx, fecha_inicio_dt):
            return False
        p = _re.resolver_parametros_regla(
            'FRANCO_FORZADO', emp.nombre,
            (fecha_inicio_dt + timedelta(days=d_idx)).isoformat(),
            reglas_servicio, emp.reglas, ajustes_reglas
        )
        return not (_re.regla_existe(p) and not _re.regla_suspendida(p))

    k_disp = sum(
        1 for lunes, dias_f in findes.items() 
        if any(_disponible(d) for d, _ in dias_f)
    )

    params_emp = _re.resolver_parametros_regla(
        'MANEJO_FINDES', emp.nombre, fecha_inicio,
        reglas_servicio, emp.reglas, ajustes_reglas
    )
    if not _re.regla_existe(params_emp) or _re.regla_suspendida(params_emp):
        print(f"{emp.nombre}: Regla excluida o suspendida")
        continue

    conf_disp = params_emp.get('por_disponibilidad', {}).get(str(k_disp), {})
    target_flr = conf_disp.get('flr', 0)
    print(f"{emp.nombre}: k_disp={k_disp}, target_flr={target_flr}")
