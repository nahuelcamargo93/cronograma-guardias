"""restricciones/hard/max_horas_semana.py — Límite máximo de horas trabajadas por semana."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import get_semanas_calendario, is_finde
import rule_engine as _re


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    semanas = get_semanas_calendario(ctx.dias, fecha_inicio_dt)
    historial = ctx.historial_semana_previa or {}

    if 'MAX_HORAS_SEMANA' not in ctx.reglas_servicio:
        return
    limite_global = ctx.reglas_servicio['MAX_HORAS_SEMANA'].get('limite', 48)

    for emp in ctx.empleados:
        hist_emp = historial.get(emp.nombre, [])
        for (iso_y, iso_w), days in semanas.items():
            fl = days[0][1]
            fecha_lunes = (fl - timedelta(days=fl.isocalendar()[2] - 1)).isoformat()
            prev_sem = [h for h in hist_emp
                        if date.fromisoformat(h['fecha']).isocalendar()[:2] == (iso_y, iso_w)]
            horas_prev = sum(h['horas'] for h in prev_sem)

            horas_sem = []
            for d, _ in days:
                td = "Finde_Feriado" if is_finde(d, ctx.offset_dia, ctx.feriados) else "Semana"
                for t in ctx.demanda_turnos.get(td, {}).keys():
                    if (emp.nombre, d, t) in ctx.turnos:
                        if t not in ctx.turnos_dict:
                            raise ValueError(f"Turno '{t}' no configurado en turnos_config.")
                        h_t = ctx.turnos_dict[t].horas
                        horas_sem.append(ctx.turnos[(emp.nombre, d, t)] * h_t)

            if horas_sem or horas_prev > 0:
                params = _re.resolver_parametros_regla(
                    'MAX_HORAS_SEMANA', emp.nombre, fecha_lunes,
                    ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
                )
                if _re.regla_existe(params):
                    limite = params.get('limite', limite_global) if isinstance(params, dict) else limite_global
                    add_hard(modelo, ctx,
                             modelo.Add(sum(horas_sem) + horas_prev <= limite),
                             f"{emp.nombre}_{iso_y}w{iso_w}")
