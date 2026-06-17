"""
restricciones/soft/equidad_fl3_fl4.py — SOFT
Minimiza la brecha de fines de semana largos (3 y 4 días) entre empleados.
Reglas: PESO_EQUIDAD_FL3, PESO_EQUIDAD_FL4
"""
from datetime import date, timedelta
import rule_engine as _re


def _bloques_largos(ctx):
    """Retorna los bloques de días consecutivos de descanso (fin de semana largo)."""
    es_descanso = [
        ((d + ctx.offset_dia) % 7 >= 5 or d in ctx.feriados)
        for d in range(ctx.dias)
    ]
    bloques = []
    actual = []
    for d in range(ctx.dias):
        if es_descanso[d]:
            actual.append(d)
        else:
            if len(actual) >= 3:
                bloques.append(actual)
            actual = []
    if len(actual) >= 3:
        bloques.append(actual)
    return bloques


def apply(modelo, ctx):
    bloques = _bloques_largos(ctx)
    max_fl3 = modelo.NewIntVar(0, 50, 'max_fl3')
    min_fl3 = modelo.NewIntVar(0, 50, 'min_fl3')
    max_fl4 = modelo.NewIntVar(0, 50, 'max_fl4')
    min_fl4 = modelo.NewIntVar(0, 50, 'min_fl4')

    totales_fl3 = []
    totales_fl4 = []

    for emp in ctx.empleados:
        fl3_mes, fl4_mes = [], []
        for bloque in bloques:
            t_f_names = ctx.demanda_turnos.get('Finde_Feriado', {}).keys()
            vars_b = [
                ctx.turnos[(emp.nombre, d, t)]
                for d in bloque for t in t_f_names
                if (emp.nombre, d, t) in ctx.turnos
            ]
            if vars_b:
                trabaja = modelo.NewBoolVar(f'trabaja_fl_{emp.nombre}_b{bloque[0]}')
                modelo.AddMaxEquality(trabaja, vars_b)
                if len(bloque) == 3:
                    fl3_mes.append(trabaja)
                elif len(bloque) >= 4:
                    fl4_mes.append(trabaja)

        params3 = _re.resolver_parametros_regla(
            'PESO_EQUIDAD_FL3', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_suspendida(params3):
            total_fl3_var = modelo.NewIntVar(0, 50, f'total_fl3_{emp.nombre}')
            modelo.Add(total_fl3_var == emp.findes_largos_3_previos + (sum(fl3_mes) if fl3_mes else 0))
            totales_fl3.append(total_fl3_var)

        params4 = _re.resolver_parametros_regla(
            'PESO_EQUIDAD_FL4', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_suspendida(params4):
            total_fl4_var = modelo.NewIntVar(0, 50, f'total_fl4_{emp.nombre}')
            modelo.Add(total_fl4_var == emp.findes_largos_4_previos + (sum(fl4_mes) if fl4_mes else 0))
            totales_fl4.append(total_fl4_var)

    if totales_fl3:
        modelo.AddMaxEquality(max_fl3, totales_fl3)
        modelo.AddMinEquality(min_fl3, totales_fl3)
        peso3 = ctx.reglas_servicio.get('PESO_EQUIDAD_FL3', {}).get('peso', 500)
        ctx.penalizaciones_soft.append((max_fl3 - min_fl3) * peso3)

    if totales_fl4:
        modelo.AddMaxEquality(max_fl4, totales_fl4)
        modelo.AddMinEquality(min_fl4, totales_fl4)
        peso4 = ctx.reglas_servicio.get('PESO_EQUIDAD_FL4', {}).get('peso', 500)
        ctx.penalizaciones_soft.append((max_fl4 - min_fl4) * peso4)

