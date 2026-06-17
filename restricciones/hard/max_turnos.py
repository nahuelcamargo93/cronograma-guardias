"""restricciones/hard/max_turnos.py — Límite máximo de un tipo de turno por semana/mes."""
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

        # 1. Límite por mes calendario
        meses = {}
        for d in range(ctx.dias):
            m_key = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m")
            meses.setdefault(m_key, []).append(d)

        for m_key, dias_m in meses.items():
            ref = (fecha_inicio_dt + timedelta(days=dias_m[0])).isoformat()
            params = _re.resolver_parametros_regla(
                'MAX_TURNOS', emp.nombre, ref,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if not _re.regla_existe(params) or not isinstance(params, list):
                continue
            for rest in params:
                max_mes = rest.get('max_por_mes')
                if max_mes is None: continue
                t_tipos = rest.get('turnos') or ([rest['turno']] if rest.get('turno') else [])
                if not t_tipos: continue
                vars_m = [ctx.turnos[(emp.nombre, d, tt)]
                          for tt in t_tipos for d in dias_m
                          if (emp.nombre, d, tt) in ctx.turnos]
                if vars_m:
                    add_hard(modelo, ctx,
                             modelo.Add(sum(vars_m) <= max_mes),
                             f"{emp.nombre}_{m_key}")

        # 2. Límite por semana
        for (iso_y, iso_w), days in semanas.items():
            fl = days[0][1]
            fecha_lunes = (fl - timedelta(days=fl.isocalendar()[2] - 1)).isoformat()
            params = _re.resolver_parametros_regla(
                'MAX_TURNOS', emp.nombre, fecha_lunes,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if not _re.regla_existe(params) or not isinstance(params, list):
                continue
            prev_sem = [h for h in hist_emp
                        if date.fromisoformat(h['fecha']).isocalendar()[:2] == (iso_y, iso_w)]
            for rest in params:
                max_sem = rest.get('max_por_semana')
                if max_sem is None: continue
                t_tipos = rest.get('turnos') or ([rest['turno']] if rest.get('turno') else [])
                if not t_tipos: continue
                prev_tipo = sum(1 for h in prev_sem if h['turno'] in t_tipos)
                vars_s = [ctx.turnos[(emp.nombre, d, tt)]
                          for tt in t_tipos for d, _ in days
                          if (emp.nombre, d, tt) in ctx.turnos]
                if vars_s or prev_tipo > 0:
                    add_hard(modelo, ctx,
                             modelo.Add(sum(vars_s) + prev_tipo <= max_sem),
                             f"{emp.nombre}_{iso_y}w{iso_w}")
