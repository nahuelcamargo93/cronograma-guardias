"""
restricciones/soft/penalizacion_turno_ausente.py — SOFT
Penaliza que en el bloque no haya ninguna semana de un tipo de turno (M/T/TN/N).
Regla: PENALIZACION_TURNO_AUSENTE
Requiere ctx.vars_turno_sem: dict {(nombre, sem_key): {M, T, TN, N: BoolVar}}
"""
import rule_engine as _re

_MAPPING_KEYS = ('M', 'T', 'TN', 'N')


def apply(modelo, ctx):
    if not hasattr(ctx, 'vars_turno_sem') or not ctx.vars_turno_sem:
        return

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'PENALIZACION_TURNO_AUSENTE', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params):
            continue
        peso = params.get('peso', 500)

        sem_vars = {k: [] for k in _MAPPING_KEYS}
        for (nombre, sem_key), v_dict in ctx.vars_turno_sem.items():
            if nombre != emp.nombre:
                continue
            for k in _MAPPING_KEYS:
                if k in v_dict:
                    sem_vars[k].append(v_dict[k])

        for t_code, svars in sem_vars.items():
            if not svars:
                continue
            is_missing = modelo.NewBoolVar(f'missing_{t_code}_{emp.nombre}')
            modelo.Add(sum(svars) == 0).OnlyEnforceIf(is_missing)
            modelo.Add(sum(svars) >= 1).OnlyEnforceIf(is_missing.Not())
            ctx.penalizaciones_soft.append(is_missing * peso)
