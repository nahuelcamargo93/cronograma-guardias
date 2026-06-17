"""restricciones/hard/min_horas_semana.py — Piso mínimo de horas trabajadas por semana.

Regla DOUBLE: soporta modo HARD (restricción dura) y SOFT (penalización proporcional al déficit).
Configuración en BD (parametros_json):
  {"min_horas": 18, "modo": "HARD", "peso_soft": 100000}
Si modo no está definido o es "HARD", se comporta como restricción dura vía add_hard.
"""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import get_semanas_calendario, is_finde
import rule_engine as _re


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
                'MIN_HORAS_SEMANA', emp.nombre, fecha_lunes,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            
            if not _re.regla_existe(params) or _re.regla_suspendida(params):
                continue
                
            min_h = params.get('min_horas', 18) if isinstance(params, dict) else 18
            modo = params.get('modo', 'HARD') if isinstance(params, dict) else 'HARD'
            peso_soft = params.get('peso_soft', 100_000) if isinstance(params, dict) else 100_000

            # Horas del historial que pertenecen a esta semana
            prev_sem = [h for h in hist_emp
                        if date.fromisoformat(h['fecha']).isocalendar()[:2] == (iso_y, iso_w)]
            horas_prev = sum(h['horas'] for h in prev_sem)

            # Variables de horas asignadas en la planificación actual para esta semana
            horas_sem = []
            for d, _ in days:
                td = "Finde_Feriado" if is_finde(d, ctx.offset_dia, ctx.feriados) else "Semana"
                for t in ctx.demanda_turnos.get(td, {}).keys():
                    if (emp.nombre, d, t) in ctx.turnos:
                        if t not in ctx.turnos_dict:
                            raise ValueError(f"Turno '{t}' no configurado en turnos_config.")
                        h_t = ctx.turnos_dict[t].horas
                        horas_sem.append(ctx.turnos[(emp.nombre, d, t)] * h_t)

            # Para evitar inviabilidad si no es físicamente posible cumplir el mínimo,
            # calculamos el límite superior teórico de horas que podría trabajar en los días activos:
            h_max_plan = 0
            for d, _ in days:
                if d in emp.dias_licencia:
                    continue  # El profesional no puede trabajar en días de licencia
                
                # Buscar el turno más largo que tiene habilitado este empleado en este día
                td = "Finde_Feriado" if is_finde(d, ctx.offset_dia, ctx.feriados) else "Semana"
                horas_posibles = [
                    ctx.turnos_dict[t].horas
                    for t in ctx.demanda_turnos.get(td, {}).keys()
                    if (emp.nombre, d, t) in ctx.turnos
                ]
                if horas_posibles:
                    h_max_plan += max(horas_posibles)

            limite_teorico = horas_prev + h_max_plan
            piso = min(min_h, limite_teorico)

            if not horas_sem and horas_prev == 0:
                continue

            if modo.upper() == "SOFT":
                # Variable entera de déficit: deficit >= piso - (sum(horas_sem) + horas_prev)
                nombre_limpio = emp.nombre.replace(" ", "_").replace(",", "")
                deficit = modelo.NewIntVar(0, piso, f"deficit_min_h_sem_{nombre_limpio}_{iso_y}w{iso_w}")
                modelo.Add(deficit >= piso - sum(horas_sem) - horas_prev)
                ctx.penalizaciones_soft.append(deficit * peso_soft)
            else:
                add_hard(modelo, ctx,
                         modelo.Add(sum(horas_sem) + horas_prev >= piso),
                         f"{emp.nombre}_{iso_y}w{iso_w}")
