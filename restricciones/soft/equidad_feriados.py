"""
restricciones/soft/equidad_feriados.py — SOFT
Penaliza de forma individual y progresiva la asignación de feriados en base al histórico de cada empleado.
Regla: PESO_EQUIDAD_FERIADOS
"""
import rule_engine as _re


def apply(modelo, ctx):
    peso = ctx.reglas_servicio.get('PESO_EQUIDAD_FERIADOS', {}).get('peso', 0)
    if peso == 0:
        return

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'PESO_EQUIDAD_FERIADOS', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_suspendida(params):
            continue

        fer_vars = []
        for d in ctx.feriados:
            if d in emp.dias_licencia:
                continue
            for t in ctx.demanda_turnos.get('Finde_Feriado', {}).keys():
                if (emp.nombre, d, t) in ctx.turnos:
                    fer_vars.append(ctx.turnos[(emp.nombre, d, t)])

        if fer_vars:
            # Penaliza linealmente cada feriado actual asignado multiplicando por (previos + 1)
            coeficiente = (emp.feriados_previos + 1) * peso
            ctx.penalizaciones_soft.append(sum(fer_vars) * coeficiente)

