"""restricciones/hard/min_findes_mes.py — Mínimo/Exacto de fines de semana trabajados por mes."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import is_finde
import rule_engine as _re


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    ref_fecha = ctx.fecha_inicio

    for emp in ctx.empleados:
        params_min = _re.resolver_parametros_regla(
            'MIN_FINDES_MES', emp.nombre, ref_fecha,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        params_exacto = _re.resolver_parametros_regla(
            'EXACTO_FINDES_MES', emp.nombre, ref_fecha,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        has_min    = _re.regla_existe(params_min) and not _re.regla_suspendida(params_min)
        has_exacto = _re.regla_existe(params_exacto) and not _re.regla_suspendida(params_exacto)
        if has_exacto and params_min is not None and _re.regla_suspendida(params_min):
            has_exacto = False
        if not has_min and not has_exacto:
            continue

        is_exact = has_exacto
        params = params_exacto if has_exacto else params_min

        # Agrupar días finde por semana
        findes = {}
        for d in range(ctx.dias):
            if is_finde(d, ctx.offset_dia, ctx.feriados):
                fecha_d = fecha_inicio_dt + timedelta(days=d)
                lunes = (fecha_d - timedelta(days=fecha_d.weekday())).isoformat()
                findes.setdefault(lunes, []).append(d)

        k = sum(1 for _, dias in findes.items() if any(d not in emp.dias_licencia for d in dias))

        if params.get('dinamico_licencias', False):
            target_f = 2 if k >= 3 else (1 if k >= 1 else 0)
        else:
            target_f = params.get('exacto_findes', params.get('min_findes', 1))

        vars_findes = []
        for lunes, dias in findes.items():
            dias_hab = []
            for d in dias:
                if d in emp.dias_licencia: continue
                fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
                p_franco = _re.resolver_parametros_regla(
                    'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                    ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
                )
                if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco): continue
                dias_hab.append(d)
            if not dias_hab: continue

            v_f = modelo.NewBoolVar(f'traba_f_{emp.nombre}_{lunes}')
            pool = [ctx.turnos[(emp.nombre, d, t)]
                    for d in dias_hab
                    for t in ctx.demanda_turnos.get("Finde_Feriado", {}).keys()
                    if (emp.nombre, d, t) in ctx.turnos]
            if pool:
                modelo.AddMaxEquality(v_f, pool)
                vars_findes.append(v_f)

        if vars_findes:
            target_real = min(target_f, len(vars_findes))
            if is_exact:
                add_hard(modelo, ctx, modelo.Add(sum(vars_findes) == target_real), emp.nombre)
            else:
                add_hard(modelo, ctx, modelo.Add(sum(vars_findes) >= target_real), emp.nombre)
