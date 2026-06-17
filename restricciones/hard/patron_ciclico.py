"""restricciones/hard/patron_ciclico.py — Patrón X días trabajo + Y días franco cíclico."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
import rule_engine as _re


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    historial = ctx.historial_semana_previa or {}

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'PATRON_CICLICO', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params): continue
        if not isinstance(params, dict): continue
        X = params.get('trabajo')
        Y = params.get('franco')
        if not X or not Y or X <= 0 or Y <= 0: continue
        L = X + Y

        offset_vars = {o: modelo.NewBoolVar(f'offset_{emp.nombre}_{o}') for o in range(L)}
        modelo.Add(sum(offset_vars.values()) == 1)

        hist_emp = historial.get(emp.nombre, [])
        if hist_emp:
            worked = {}
            for h in hist_emp:
                delta = (date.fromisoformat(h['fecha']) - fecha_inicio_dt).days
                if -L <= delta <= -1: worked[delta] = True
            if worked:
                conflicts = {}
                for o in range(L):
                    conflicts[o] = sum(
                        1 for d in range(-L, 0)
                        if ((1 if (d + o) % L < X else 0) != (1 if worked.get(d) else 0))
                    )
                min_c = min(conflicts.values())
                for o in range(L):
                    if conflicts[o] > min_c:
                        modelo.Add(offset_vars[o] == 0)

        for d in range(ctx.dias):
            turnos_hoy = [v for (n, dia, t), v in ctx.turnos.items() if n == emp.nombre and dia == d]
            if not turnos_hoy or d in emp.dias_licencia: continue
            fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            p_franco = _re.resolver_parametros_regla(
                'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco): continue
            rhs = [offset_vars[o] for o in range(L) if (d + o) % L < X]
            add_hard(modelo, ctx, modelo.Add(sum(turnos_hoy) == sum(rhs)), f"{emp.nombre}_d{d}")
