"""
restricciones/soft/equidad_finds_anual.py — SOFT
Minimiza la brecha del ratio anual (histórico + actual) de fins de semana trabajados.
Regla: PESO_EQUIDAD_FINDES_ANUAL
"""
from datetime import date, timedelta
import rule_engine as _re


def apply(modelo, ctx):
    peso_cfg = ctx.reglas_servicio.get('PESO_EQUIDAD_FINDES_ANUAL') or ctx.reglas_servicio.get('EQUIDAD_FINDES_ANUAL', {})
    peso = peso_cfg.get('peso', 500) if isinstance(peso_cfg, dict) else 500

    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    max_ratio = modelo.NewIntVar(0, 1000, 'max_ratio_finde_anual')
    min_ratio = modelo.NewIntVar(0, 1000, 'min_ratio_finde_anual')

    dias_por_semana = {}
    for d in range(ctx.dias):
        lunes = (fecha_inicio_dt + timedelta(days=d))
        lunes = lunes - timedelta(days=lunes.weekday())
        dias_por_semana.setdefault(lunes.isoformat(), []).append(d)

    ratios_lista = []

    for emp in ctx.empleados:
        codigo_activo = 'PESO_EQUIDAD_FINDES_ANUAL' if 'PESO_EQUIDAD_FINDES_ANUAL' in ctx.reglas_servicio else 'EQUIDAD_FINDES_ANUAL'
        params = _re.resolver_parametros_regla(
            codigo_activo, emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_suspendida(params):
            continue

        finds_trab_mes = []
        finds_hab_mes = 0

        for sem_key, dias_sem in dias_por_semana.items():
            sem_id = sem_key.replace('-', '_')
            sabados = [d for d in dias_sem if (d + ctx.offset_dia) % 7 == 5]
            domingos = [d for d in dias_sem if (d + ctx.offset_dia) % 7 == 6]
            if not sabados or not domingos:
                continue
            s, dom = sabados[0], domingos[0]
            if s not in emp.dias_licencia and dom not in emp.dias_licencia:
                finds_hab_mes += 1
            t_f_names = ctx.demanda_turnos.get('Finde_Feriado', {}).keys()
            vars_f = (
                [ctx.turnos[(emp.nombre, s, t)] for t in t_f_names if (emp.nombre, s, t) in ctx.turnos] +
                [ctx.turnos[(emp.nombre, dom, t)] for t in t_f_names if (emp.nombre, dom, t) in ctx.turnos]
            )
            if vars_f:
                traba = modelo.NewBoolVar(f'traba_finde_anual_{emp.nombre}_{sem_id}')
                modelo.AddMaxEquality(traba, vars_f)
                finds_trab_mes.append(traba)

        f_trab_total = emp.findes_semanas_previos + (sum(finds_trab_mes) if finds_trab_mes else 0)
        f_hab_total = emp.findes_habiles_previos + finds_hab_mes

        ratio = modelo.NewIntVar(0, 1000, f'ratio_finde_anual_{emp.nombre}')
        if f_hab_total > 0:
            modelo.Add(ratio * f_hab_total <= f_trab_total * 1000)
            modelo.Add(ratio * f_hab_total > (f_trab_total * 1000) - f_hab_total)
        else:
            modelo.Add(ratio == 0)

        params_activo = _re.resolver_parametros_regla(
            codigo_activo, emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_suspendida(params_activo):
            ratios_lista.append(ratio)

    if ratios_lista:
        modelo.AddMaxEquality(max_ratio, ratios_lista)
        modelo.AddMinEquality(min_ratio, ratios_lista)
        brecha = modelo.NewIntVar(0, 1000, 'brecha_ratio_finde_anual')
        modelo.Add(brecha == max_ratio - min_ratio)
        ctx.penalizaciones_soft.append(brecha * peso)

