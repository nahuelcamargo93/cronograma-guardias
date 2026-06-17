"""restricciones/hard/fin_licencia.py — Obliga a trabajar el día siguiente al fin de una licencia."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import is_finde
import rule_engine as _re


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    ref_fecha = ctx.fecha_inicio

    for emp in ctx.empleados:
        p_fin = _re.resolver_parametros_regla(
            'FIN_LICENCIA', emp.nombre, ref_fecha, ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(p_fin) or _re.regla_suspendida(p_fin):
            continue

        for d in range(ctx.dias - 1):
            if d in emp.dias_licencia and (d + 1) not in emp.dias_licencia:
                fecha_sig = (fecha_inicio_dt + timedelta(days=d + 1)).isoformat()
                p_franco = _re.resolver_parametros_regla(
                    'FRANCO_FORZADO', emp.nombre, fecha_sig,
                    ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
                )
                if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                    continue
                td_sig = "Finde_Feriado" if is_finde(d + 1, ctx.offset_dia, ctx.feriados) else "Semana"
                vars_sig = [ctx.turnos[(emp.nombre, d + 1, t)]
                            for t in ctx.demanda_turnos.get(td_sig, {}).keys()
                            if (emp.nombre, d + 1, t) in ctx.turnos]
                if vars_sig:
                    add_hard(modelo, ctx,
                             modelo.Add(sum(vars_sig) >= 1),
                             f"{emp.nombre}_d{d+1}")
