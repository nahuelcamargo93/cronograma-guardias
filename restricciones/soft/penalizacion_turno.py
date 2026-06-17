"""
restricciones/soft/penalizacion_turno.py — SOFT
Penaliza asignaciones a un turno concreto con peso configurable por DB.
Regla: PENALIZACION_TURNO
"""
import rule_engine as _re


def apply(modelo, ctx):
    es_descanso = [
        ((d + ctx.offset_dia) % 7 >= 5 or d in ctx.feriados)
        for d in range(ctx.dias)
    ]
    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'PENALIZACION_TURNO', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(params):
            continue
        items = params if isinstance(params, list) else [params]
        for item in items:
            t_pen = item.get('turno')
            peso = item.get('peso', 100)
            solo_semana = item.get('solo_semana', False)
            solo_finde = item.get('solo_finde', False)
            dias_validos = item.get('dias')
            if not t_pen:
                continue
            for d in range(ctx.dias):
                if (emp.nombre, d, t_pen) not in ctx.turnos:
                    continue
                aplica = True
                if solo_semana and es_descanso[d]:
                    aplica = False
                if solo_finde and not es_descanso[d]:
                    aplica = False
                if dias_validos is not None:
                    dia_sem = (d + ctx.offset_dia) % 7
                    if dia_sem not in dias_validos:
                        aplica = False
                if aplica:
                    ctx.penalizaciones_soft.append(
                        ctx.turnos[(emp.nombre, d, t_pen)] * peso
                    )
