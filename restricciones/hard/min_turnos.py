"""restricciones/hard/min_turnos.py — Mínimo de un tipo de turno por semana."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import get_semanas_calendario
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
            params = _re.resolver_parametros_regla(
                'MIN_TURNOS', emp.nombre, fecha_lunes,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if not _re.regla_existe(params) or not isinstance(params, list):
                continue
            prev_sem = [h for h in hist_emp
                        if date.fromisoformat(h['fecha']).isocalendar()[:2] == (iso_y, iso_w)]
            for rest in params:
                t_tipo = rest.get('turno')
                min_sem = rest.get('min_por_semana', 0)
                if not t_tipo or min_sem <= 0: continue
                prev_tipo = sum(1 for h in prev_sem if h['turno'] == t_tipo)
                vars_t = [ctx.turnos[(emp.nombre, d, t_tipo)]
                          for d, _ in days
                          if (emp.nombre, d, t_tipo) in ctx.turnos
                          and d not in emp.dias_licencia]
                if vars_t:
                    efectivo = min(min_sem, len(vars_t) + prev_tipo)
                    add_hard(modelo, ctx,
                             modelo.Add(sum(vars_t) + prev_tipo >= efectivo),
                             f"{emp.nombre}_{iso_y}w{iso_w}_{t_tipo}")
