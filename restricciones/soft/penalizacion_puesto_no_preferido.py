"""
restricciones/soft/penalizacion_puesto_no_preferido.py — SOFT
Penaliza asignaciones a puestos no primarios del empleado.
Regla: PENALIZACION_PUESTO_NO_PREFERIDO
"""
import rule_engine as _re


def apply(modelo, ctx):
    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'PENALIZACION_PUESTO_NO_PREFERIDO', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(params) or not emp.puestos_primarios:
            continue
        peso = params.get('peso', 500) if isinstance(params, dict) else 500
        priorizar_cat = params.get('priorizar_categoria') if isinstance(params, dict) else None

        multiplicador = 1
        if priorizar_cat in ('asc', 'desc'):
            try:
                val_cat = int(emp.categoria)
                cats = []
                for e in ctx.empleados:
                    if e.rol == emp.rol:
                        try:
                            cats.append(int(e.categoria))
                        except (ValueError, TypeError):
                            pass
                if cats:
                    max_cat, min_cat = max(cats), min(cats)
                    if priorizar_cat == 'desc':
                        multiplicador = max_cat - val_cat + 1
                    else:
                        multiplicador = val_cat - min_cat + 1
            except (ValueError, TypeError):
                pass

        for (n, d, t_nombre), var_turno in ctx.turnos.items():
            if n != emp.nombre:
                continue
            turno_obj = ctx.turnos_dict.get(t_nombre)
            if turno_obj is None:
                continue
            puesto_del_turno = turno_obj.puesto_nombre
            if puesto_del_turno and puesto_del_turno not in emp.puestos_primarios:
                ctx.penalizaciones_soft.append(var_turno * (peso * multiplicador))
