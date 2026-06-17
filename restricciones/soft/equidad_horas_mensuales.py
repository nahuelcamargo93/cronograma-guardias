"""
restricciones/soft/equidad_horas_mensuales.py — SOFT
Nivelación de horas del bloque: minimiza la brecha max-min entre empleados.
Regla: PESO_BRECHA_MENSUAL
"""
from datetime import date, timedelta
import rule_engine as _re


def apply(modelo, ctx):
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    es_descanso = [
        ((d + ctx.offset_dia) % 7 >= 5 or d in ctx.feriados)
        for d in range(ctx.dias)
    ]

    limite = ctx.reglas_servicio.get('LIMITES_SOFT_RULES', {}).get('MAX_HORAS_LIMITE_BASE', 200)
    max_horas_mes = modelo.NewIntVar(0, limite, 'eq_horas_max')
    min_horas_mes = modelo.NewIntVar(0, limite, 'eq_horas_min')

    horas_totales = []

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'PESO_BRECHA_MENSUAL', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_suspendida(params):
            continue

        horas_vars = []
        for d in range(ctx.dias):
            tipo = 'Finde_Feriado' if es_descanso[d] else 'Semana'
            for t in ctx.demanda_turnos.get(tipo, {}).keys():
                if (emp.nombre, d, t) in ctx.turnos:
                    h = 12 if (es_descanso[d] or t.startswith('Noche')) else 6
                    horas_vars.append(ctx.turnos[(emp.nombre, d, t)] * h)

        if horas_vars:
            total_hs_var = modelo.NewIntVar(0, limite, f'eq_horas_{emp.nombre}')
            modelo.Add(total_hs_var == sum(horas_vars))
            horas_totales.append(total_hs_var)

    if horas_totales:
        modelo.AddMaxEquality(max_horas_mes, horas_totales)
        modelo.AddMinEquality(min_horas_mes, horas_totales)
        peso = ctx.reglas_servicio.get('PESO_BRECHA_MENSUAL', {}).get('peso', 50)
        brecha = modelo.NewIntVar(0, limite, 'brecha_mensual')
        modelo.Add(brecha == max_horas_mes - min_horas_mes)
        ctx.penalizaciones_soft.append(brecha * peso)

