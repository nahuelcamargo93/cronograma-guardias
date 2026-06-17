"""restricciones/double/no_repetir_n_consecutivo.py — Máximo una semana con turno N por mes.

Esta regla limita la cantidad de semanas en las que un profesional puede
tener asignado el turno N (Noche) en el transcurso del mes planificado.
Asegura que no se asigne el turno N en 2 o más semanas del mismo mes.
"""
from datetime import date, timedelta
from restricciones.cargador import add_hard
import rule_engine as _re


def apply(modelo, ctx) -> None:
    if not hasattr(ctx, 'vars_turno_sem') or not ctx.vars_turno_sem:
        return

    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    dias_por_semana = {}
    for d in range(ctx.dias):
        fd = fecha_inicio_dt + timedelta(days=d)
        lunes = (fd - timedelta(days=fd.weekday())).isoformat()
        dias_por_semana.setdefault(lunes, []).append(d)

    semanas_keys = sorted(dias_por_semana.keys())
    if not semanas_keys:
        return

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'NO_REPETIR_N_CONSECUTIVO', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params):
            continue

        modo = params.get('modo', 'HARD').upper()
        peso_soft = params.get('peso_soft', 5000)

        # Buscar las variables semanales de N para las semanas del mes
        vars_n_semanales = []
        for sem_key in semanas_keys:
            v_dict = ctx.vars_turno_sem.get((emp.nombre, sem_key))
            if v_dict and 'N' in v_dict:
                vars_n_semanales.append(v_dict['N'])

        if not vars_n_semanales:
            continue

        sum_semanas_N = sum(vars_n_semanales)

        if modo == 'HARD':
            # Máximo 1 semana con turno N
            add_hard(modelo, ctx,
                     modelo.Add(sum_semanas_N <= 1),
                     f"{emp.nombre}_max_1_sem_N")
        else:
            # Penalizar si es >= 2 (violacion >= sum_semanas_N - 1)
            violacion = modelo.NewIntVar(0, len(semanas_keys), f"viol_max_sem_n_{emp.nombre}")
            modelo.Add(violacion >= sum_semanas_N - 1)
            ctx.penalizaciones_soft.append(violacion * peso_soft)
