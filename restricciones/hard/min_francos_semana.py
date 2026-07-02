"""restricciones/hard/min_francos_semana.py — Piso mínimo de francos por semana calendario.

Esta regla asegura que el profesional tenga al menos una cantidad mínima de francos en cada semana
calendario. Permite configurar modo HARD o SOFT y contempla las licencias del profesional como días
trabajados en dicha semana (es decir, no cuentan como francos), reduciendo de forma segura el mínimo
requerido de francos para evitar inviabilidades.
"""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import get_semanas_calendario, is_finde
import database.queries as q
import rule_engine as _re

def es_fecha_licencia(nombre: str, fecha_dt: date) -> bool:
    for licencias in (q.LAR, q.LPP, q.LM, q.CM):
        for (lic_ini_str, lic_fin_str) in licencias.get(nombre, []):
            if date.fromisoformat(lic_ini_str) <= fecha_dt <= date.fromisoformat(lic_fin_str):
                return True
    return False

def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    semanas = get_semanas_calendario(ctx.dias, fecha_inicio_dt)
    historial = ctx.historial_semana_previa or {}

    for emp in ctx.empleados:
        hist_emp = historial.get(emp.nombre, [])
        for (iso_y, iso_w), days in semanas.items():
            fl = days[0][1]
            fecha_lunes = (fl - timedelta(days=fl.isocalendar()[2] - 1)).isoformat()
            
            # Obtener parámetros para el empleado y la semana correspondiente
            params = _re.resolver_parametros_regla(
                'MIN_FRANCOS_SEMANA', emp.nombre, fecha_lunes,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            
            if not _re.regla_existe(params) or _re.regla_suspendida(params):
                continue
                
            min_francos = params.get('min_francos', 2) if isinstance(params, dict) else 2
            modo = params.get('modo', 'HARD').upper() if isinstance(params, dict) else 'HARD'
            peso_soft = params.get('peso_soft', 100_000) if isinstance(params, dict) else 100_000

            # 1. Contar francos en el historial
            # Un día en el historial es franco si:
            # - Cae en esta semana calendario (antes de fecha_inicio_dt).
            # - No fue de licencia (es_fecha_licencia es False).
            # - No se trabajó (no hay guardia asignada en el historial para esa fecha).
            lunes_dt = fl - timedelta(days=fl.isocalendar()[2] - 1)
            francos_prev = 0
            licencias_prev = 0
            turnos_prev = 0
            dias_prev = 0
            
            for offset in range(7):
                dia_semana_dt = lunes_dt + timedelta(days=offset)
                if dia_semana_dt < fecha_inicio_dt:
                    dias_prev += 1
                    if es_fecha_licencia(emp.nombre, dia_semana_dt):
                        licencias_prev += 1
                    else:
                        fecha_str = dia_semana_dt.isoformat()
                        trabajo = [h for h in hist_emp if h['fecha'] == fecha_str and h.get('turno') != 'FCG']
                        if trabajo:
                            turnos_prev += 1
                        else:
                            francos_prev += 1

            # Escalar el requerimiento si la semana calendario está incompleta (bordes del mes)
            dias_conocidos = len(days) + dias_prev
            if dias_conocidos < 7:
                min_francos_req = round(min_francos * dias_conocidos / 7)
            else:
                min_francos_req = min_francos

            # 2. Francos de la planificación actual
            # Un día es franco si:
            # - No está de licencia (emp.dias_licencia).
            # - No trabaja (la suma de variables de turnos es 0).
            francos_sem = []
            licencias_plan = 0
            
            for d, _ in days:
                if d in emp.dias_licencia:
                    licencias_plan += 1
                    continue # Las licencias cuentan como días trabajados (no son francos)
                
                td = "Finde_Feriado" if is_finde(d, ctx.offset_dia, ctx.feriados) else "Semana"
                turnos_dia = [ctx.turnos[(emp.nombre, d, t)]
                              for t in ctx.demanda_turnos.get(td, {}).keys()
                              if (emp.nombre, d, t) in ctx.turnos]
                
                if turnos_dia:
                    is_work = sum(turnos_dia)
                    is_franco = modelo.NewBoolVar(f"min_franco_{emp.nombre}_d{d}_{iso_y}w{iso_w}")
                    modelo.Add(is_franco == 1 - is_work)
                    francos_sem.append(is_franco)
                else:
                    francos_sem.append(1)

            # Para evitar inviabilidades, ajustamos el piso
            licencias_totales = licencias_prev + licencias_plan
            max_francos_posibles = 7 - licencias_totales - turnos_prev
            max_francos_posibles = max(0, max_francos_posibles)
            
            piso = min(min_francos_req, max_francos_posibles)

            total_francos = sum(francos_sem) + francos_prev

            if modo == "SOFT":
                nombre_limpio = emp.nombre.replace(" ", "_").replace(",", "")
                deficit = modelo.NewIntVar(0, piso, f"deficit_min_fr_sem_{nombre_limpio}_{iso_y}w{iso_w}")
                modelo.Add(deficit >= piso - total_francos)
                ctx.penalizaciones_soft.append(deficit * peso_soft)
            else:
                add_hard(modelo, ctx,
                         modelo.Add(total_francos >= piso),
                         f"{emp.nombre}_{iso_y}w{iso_w}")
