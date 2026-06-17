"""restricciones/hard/orden_rotacion_semanal.py — HARD
Fuerza a que los turnos semanales sigan la rotación ideal: T -> M -> N -> TN -> T.
Regla: ORDEN_ROTACION_SEMANAL
"""
from datetime import date, timedelta
import rule_engine as _re
from restricciones.cargador import add_hard
from restricciones.hard._utils import determinar_familia_ganadora

_IDEAL_TRANSITIONS = {
    'T': 'M',
    'M': 'N',
    'N': 'TN',
    'TN': 'T'
}


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

    primer_lunes = date.fromisoformat(semanas_keys[0])

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'ORDEN_ROTACION_SEMANAL', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params):
            continue

        nombre = emp.nombre
        hist_prev = ctx.historial_semana_previa.get(nombre, []) if ctx.historial_semana_previa else []

        # 1. Transición de la semana previa a la primera semana planificada
        ganador_prev = determinar_familia_ganadora(hist_prev, primer_lunes - timedelta(days=7))
        if ganador_prev and ganador_prev in _IDEAL_TRANSITIONS:
            ideal_sig = _IDEAL_TRANSITIONS[ganador_prev]
            v_dict_first = ctx.vars_turno_sem.get((nombre, semanas_keys[0]))
            if v_dict_first:
                for k in ['M', 'T', 'TN', 'N']:
                    if k != ideal_sig and k in v_dict_first:
                        add_hard(modelo, ctx,
                                 modelo.Add(v_dict_first[k] == 0),
                                 f"{nombre}_prev_to_{semanas_keys[0]}_{ganador_prev}_bad_{k}")

        # 2. Transiciones entre semanas dentro del período de planificación
        for idx in range(len(semanas_keys) - 1):
            sem_actual = semanas_keys[idx]
            sem_siguiente = semanas_keys[idx + 1]

            v_dict_act = ctx.vars_turno_sem.get((nombre, sem_actual))
            v_dict_sig = ctx.vars_turno_sem.get((nombre, sem_siguiente))

            if v_dict_act and v_dict_sig:
                for f1 in ['M', 'T', 'TN', 'N']:
                    if f1 not in v_dict_act or f1 not in _IDEAL_TRANSITIONS:
                        continue
                    ideal_sig = _IDEAL_TRANSITIONS[f1]
                    for f2 in ['M', 'T', 'TN', 'N']:
                        if f2 not in v_dict_sig or f2 == ideal_sig:
                            continue
                        
                        add_hard(modelo, ctx,
                                 modelo.Add(v_dict_act[f1] + v_dict_sig[f2] <= 1),
                                 f"{nombre}_{sem_actual}_{sem_siguiente}_bad_rot_{f1}_{f2}")
