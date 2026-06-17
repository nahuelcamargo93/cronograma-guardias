"""restricciones/hard/max_dias_continuos.py — Límite de días de trabajo consecutivos."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import is_finde
import rule_engine as _re


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    historial = ctx.historial_semana_previa or {}

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'MAX_DIAS_CONTINUOS', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_suspendida(params): continue
        max_dias = params.get('max_dias') if isinstance(params, dict) else None
        if not max_dias or max_dias <= 0: continue

        traba_dia = {}
        for d in range(ctx.dias):
            td = "Finde_Feriado" if is_finde(d, ctx.offset_dia, ctx.feriados) else "Semana"
            t_dia = [ctx.turnos[(emp.nombre, d, t)]
                     for t in ctx.demanda_turnos.get(td, {}).keys()
                     if (emp.nombre, d, t) in ctx.turnos]
            if t_dia:
                v = modelo.NewBoolVar(f"traba_dia_{emp.nombre}_d{d}")
                modelo.Add(v == sum(t_dia))
                traba_dia[d] = v
            else:
                traba_dia[d] = 0

        hist_emp = historial.get(emp.nombre, [])
        worked_hist = {h['fecha'] for h in hist_emp}
        T = {}
        for d in range(-max_dias, ctx.dias):
            if d < 0:
                fecha_h = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m-%d")
                T[d] = 1 if fecha_h in worked_hist else 0
            else:
                T[d] = traba_dia[d]

        window = max_dias + 1
        for start in range(-max_dias, ctx.dias - max_dias):
            win = [T[d] for d in range(start, start + window)]
            add_hard(modelo, ctx,
                     modelo.Add(sum(win) <= max_dias),
                     f"{emp.nombre}_w{start}")
