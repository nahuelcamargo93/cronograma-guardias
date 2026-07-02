"""
restricciones/soft/equidad_feriados.py — SOFT
Penaliza de forma individual y progresiva la asignación de feriados en base al histórico de cada empleado.
Regla: PESO_EQUIDAD_FERIADOS
"""
import rule_engine as _re


def apply(modelo, ctx):
    peso_cfg = ctx.reglas_servicio.get('PESO_EQUIDAD_FERIADOS') or ctx.reglas_servicio.get('EQUIDAD_FERIADOS', {})
    peso = peso_cfg.get('peso', 0) if isinstance(peso_cfg, dict) else 0
    if peso == 0:
        return

    codigo_activo = 'PESO_EQUIDAD_FERIADOS' if 'PESO_EQUIDAD_FERIADOS' in ctx.reglas_servicio else 'EQUIDAD_FERIADOS'
    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            codigo_activo, emp.nombre, ctx.fecha_inicio,
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

