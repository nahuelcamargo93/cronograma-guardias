"""restricciones/hard/personal_asociado.py — Parejas de personal que deben coincidir en franjas horarias."""
from restricciones.cargador import add_hard
from restricciones.hard._utils import is_finde
import rule_engine as _re


def apply(modelo, ctx) -> None:
    params = _re.resolver_parametros_regla(
        'PERSONAL_ASOCIADO', 'GLOBAL', ctx.fecha_inicio, ctx.reglas_servicio, {}, {}
    )
    if not _re.regla_existe(params) or _re.regla_suspendida(params):
        return

    emp_names = {e.nombre for e in ctx.empleados}
    for p1_name, p2_name in params.get('parejas', []):
        if p1_name not in emp_names or p2_name not in emp_names:
            continue
        for d in range(ctx.dias):
            td = "Finde_Feriado" if is_finde(d, ctx.offset_dia, ctx.feriados) else "Semana"
            franjas = {}
            for t in ctx.demanda_turnos.get(td, {}).keys():
                t_info = ctx.turnos_dict.get(t)
                if t_info:
                    franjas.setdefault((t_info.hora_inicio, t_info.horas), []).append(t)
            for _, turnos_f in franjas.items():
                vars1 = [ctx.turnos[(p1_name, d, t)] for t in turnos_f if (p1_name, d, t) in ctx.turnos]
                vars2 = [ctx.turnos[(p2_name, d, t)] for t in turnos_f if (p2_name, d, t) in ctx.turnos]
                add_hard(modelo, ctx,
                         modelo.Add(sum(vars1) == sum(vars2)),
                         f"{p1_name}_{p2_name}_d{d}")
