"""
restricciones/soft/turnos_preferenciales.py — SOFT
Bonifica asignaciones que coinciden con el turno preferido por día de semana.
Regla: TURNOS_PREFERENCIALES
"""
import rule_engine as _re

_MAPA_DIAS = {
    'Lunes': 0, 'Martes': 1, 'Miercoles': 2,
    'Jueves': 3, 'Viernes': 4, 'Sabado': 5, 'Domingo': 6,
}


def apply(modelo, ctx):
    es_descanso = [
        ((d + ctx.offset_dia) % 7 >= 5 or d in ctx.feriados)
        for d in range(ctx.dias)
    ]
    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'TURNOS_PREFERENCIALES', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_suspendida(params) or not isinstance(params, list):
            continue
        for pref in params:
            dia_objetivo = _MAPA_DIAS.get(pref.get('Dia'))
            if dia_objetivo is None:
                continue
            turno_pref = pref['Turno'].replace(' ', '_')
            for d in range(ctx.dias):
                if (d + ctx.offset_dia) % 7 != dia_objetivo:
                    continue
                if d in emp.dias_licencia:
                    continue
                tipo_dia = 'Finde_Feriado' if es_descanso[d] else 'Semana'
                vars_pref = [
                    ctx.turnos[(emp.nombre, d, t)]
                    for t in ctx.demanda_turnos.get(tipo_dia, {}).keys()
                    if (emp.nombre, d, t) in ctx.turnos
                    and (t == turno_pref or t.startswith(turno_pref + '_'))
                ]
                if vars_pref:
                    cumple = modelo.NewBoolVar(
                        f'pref_{emp.nombre}_d{d}_{turno_pref}'
                    )
                    modelo.Add(sum(vars_pref) == 1).OnlyEnforceIf(cumple)
                    modelo.Add(sum(vars_pref) == 0).OnlyEnforceIf(cumple.Not())
                    ctx.bonuses_soft.append(cumple)
