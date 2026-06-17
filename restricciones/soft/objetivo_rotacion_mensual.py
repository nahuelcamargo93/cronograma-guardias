"""
restricciones/soft/objetivo_rotacion_mensual.py — SOFT
Penaliza desvíos respecto a un objetivo de semanas por tipo de turno (M/T/TN/N).
Regla: OBJETIVO_ROTACION_MENSUAL
Requiere ctx.vars_turno_sem: dict {(nombre, sem_key): {M, T, TN, N: BoolVar}}
"""
import rule_engine as _re


def apply(modelo, ctx):
    if not hasattr(ctx, 'vars_turno_sem') or not ctx.vars_turno_sem:
        return

    _MAPPING_KEYS = ('M', 'T', 'TN', 'N')

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'OBJETIVO_ROTACION_MENSUAL', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params):
            continue
        objetivos = params.get('objetivos', {})
        peso = params.get('peso', 100)

        # Agrupar BoolVars de tipo de semana para este empleado
        sem_vars = {k: [] for k in _MAPPING_KEYS}
        for (nombre, sem_key), v_dict in ctx.vars_turno_sem.items():
            if nombre != emp.nombre:
                continue
            for k in _MAPPING_KEYS:
                if k in v_dict:
                    sem_vars[k].append(v_dict[k])

        for t_code, target in objetivos.items():
            svars = sem_vars.get(t_code, [])
            if not svars:
                continue
            total_t = sum(svars)
            diff = modelo.NewIntVar(0, 10, f'diff_rot_{t_code}_{emp.nombre}')
            modelo.AddAbsEquality(diff, total_t - target)
            ctx.penalizaciones_soft.append(diff * peso)
