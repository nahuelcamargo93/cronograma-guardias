"""restricciones/hard/balance_dia_noche.py — Prohíbe que noche supere a día en el mismo día."""
from restricciones.cargador import add_hard
from restricciones.hard._utils import is_finde
from utils import time_to_float
import rule_engine as _re


def apply(modelo, ctx) -> None:
    ref_fecha = ctx.fecha_inicio
    p_regla = _re.resolver_parametros_regla(
        'MAX_NOCHE_VS_DIA', 'GLOBAL', ref_fecha, ctx.reglas_servicio, {}, {}
    )
    if not _re.regla_existe(p_regla) or _re.regla_suspendida(p_regla):
        return

    for d in range(ctx.dias):
        td = "Finde_Feriado" if is_finde(d, ctx.offset_dia, ctx.feriados) else "Semana"
        vars_dia, vars_noche = [], []
        for t in ctx.demanda_turnos.get(td, {}).keys():
            if t not in ctx.turnos_dict: continue
            hi = time_to_float(ctx.turnos_dict[t].hora_inicio)
            if ctx.turnos_dict[t].horas >= 20: continue
            es_noche = hi >= 18.0 or hi < 5.0
            for emp in ctx.empleados:
                if (emp.nombre, d, t) in ctx.turnos:
                    (vars_noche if es_noche else vars_dia).append(ctx.turnos[(emp.nombre, d, t)])

        if vars_noche:
            if vars_dia:
                add_hard(modelo, ctx, modelo.Add(sum(vars_noche) <= sum(vars_dia)), f"d{d}")
            else:
                add_hard(modelo, ctx, modelo.Add(sum(vars_noche) == 0), f"d{d}")
