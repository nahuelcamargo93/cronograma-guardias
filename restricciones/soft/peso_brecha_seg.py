"""
restricciones/soft/peso_brecha_seg.py — SOFT
Nivelación de semanas de seguimiento: minimiza la brecha max-min entre empleados.
Regla: PESO_BRECHA_SEG
"""
import rule_engine as _re


def apply(modelo, ctx):
    if not hasattr(ctx, 'vars_seg_emp') or not ctx.vars_seg_emp:
        return

    # Determinamos el límite superior para las semanas de seguimiento (típicamente 5 o 6 semanas)
    limite = ctx.num_semanas
    max_segs = modelo.NewIntVar(0, limite, 'eq_segs_max')
    min_segs = modelo.NewIntVar(0, limite, 'eq_segs_min')

    segs_totales = []

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'PESO_BRECHA_SEG', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_suspendida(params):
            continue

        # Si el empleado no tiene registradas variables de seguimiento (ej. no evalúa BONUS_SEG_TOTAL), se lo excluye
        vars_emp = ctx.vars_seg_emp.get(emp.nombre, [])
        if vars_emp:
            total_segs_var = modelo.NewIntVar(0, limite, f'eq_segs_{emp.nombre}')
            modelo.Add(total_segs_var == sum(vars_emp))
            segs_totales.append(total_segs_var)

    if segs_totales:
        modelo.AddMaxEquality(max_segs, segs_totales)
        modelo.AddMinEquality(min_segs, segs_totales)
        peso = ctx.reglas_servicio.get('PESO_BRECHA_SEG', {}).get('peso', 100)
        brecha = modelo.NewIntVar(0, limite, 'brecha_seg')
        modelo.Add(brecha == max_segs - min_segs)
        ctx.penalizaciones_soft.append(brecha * peso)
