"""
restricciones/soft/equidad_tipo_turno.py — SOFT
Minimiza la brecha de semanas por tipo (M/T/TN/N) entre empleados.
Regla: PESO_EQUIDAD_TIPO_TURNO
Requiere ctx.vars_turno_sem: dict {(nombre, sem_key): {M, T, TN, N: BoolVar}}
"""
import rule_engine as _re

_TIPOS = ('M', 'T', 'TN', 'N')


def apply(modelo, ctx):
    if not hasattr(ctx, 'vars_turno_sem') or not ctx.vars_turno_sem:
        return
    if 'PESO_EQUIDAD_TIPO_TURNO' not in ctx.reglas_servicio:
        return
    peso = ctx.reglas_servicio['PESO_EQUIDAD_TIPO_TURNO'].get('peso', 150)
    if peso == 0:
        return


    max_vars = {k: modelo.NewIntVar(0, 10, f'max_sem_{k}') for k in _TIPOS}
    min_vars = {k: modelo.NewIntVar(0, 10, f'min_sem_{k}') for k in _TIPOS}

    totales_por_tipo = {k: [] for k in _TIPOS}

    for emp in ctx.empleados:
        for t_code in _TIPOS:
            svars = [
                v_dict[t_code]
                for (nombre, _), v_dict in ctx.vars_turno_sem.items()
                if nombre == emp.nombre and t_code in v_dict
            ]
            if svars:
                total_var = modelo.NewIntVar(0, 10, f'tot_{t_code}_{emp.nombre}')
                modelo.Add(total_var == sum(svars))
                totales_por_tipo[t_code].append(total_var)

    for t_code in _TIPOS:
        if totales_por_tipo[t_code]:
            modelo.AddMaxEquality(max_vars[t_code], totales_por_tipo[t_code])
            modelo.AddMinEquality(min_vars[t_code], totales_por_tipo[t_code])
        else:
            modelo.Add(max_vars[t_code] == 0)
            modelo.Add(min_vars[t_code] == 0)

    brecha = sum(
        max_vars[k] - min_vars[k] for k in _TIPOS
    )
    ctx.penalizaciones_soft.append(brecha * peso)
