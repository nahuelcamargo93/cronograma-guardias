"""
restricciones/soft/bonus_carga_perfecta.py — SOFT
Bonifica cuando el total de horas mensuales (efectivas + licencia prorrateada)
cae dentro de [min_h, max_h] configurados en la DB.
Regla: BONUS_POR_CARGA_PERFECTA
"""
from datetime import date, timedelta
import rule_engine as _re


def apply(modelo, ctx):
    if not ctx.turnos_dict:
        return
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    es_descanso = [
        ((d + ctx.offset_dia) % 7 >= 5 or d in ctx.feriados)
        for d in range(ctx.dias)
    ]

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'BONUS_POR_CARGA_PERFECTA', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params):
            continue
        min_h = params.get('min_h', 142)
        max_h = params.get('max_h', 146)
        bonus_val = params.get('bonus', 2000)

        meses = {}
        for d in range(ctx.dias):
            m_key = (fecha_inicio_dt + timedelta(days=d)).strftime('%Y-%m')
            meses.setdefault(m_key, []).append(d)

        for m_key, dias_m in meses.items():
            h_vars_m = []
            for d in dias_m:
                tipo = 'Finde_Feriado' if es_descanso[d] else 'Semana'
                for t in ctx.demanda_turnos.get(tipo, {}).keys():
                    if (emp.nombre, d, t) in ctx.turnos:
                        h_t = ctx.turnos_dict[t].horas if t in ctx.turnos_dict else 6
                        h_vars_m.append(ctx.turnos[(emp.nombre, d, t)] * h_t)

            dias_lic_m = [d for d in dias_m if d in emp.dias_licencia]
            val_dia = 144.0 / ctx.dias
            h_lic_m = int(val_dia * len(dias_lic_m) + 0.5)

            total_h = modelo.NewIntVar(0, 500, f'h_mes_{emp.nombre}_{m_key}')
            modelo.Add(total_h == sum(h_vars_m) + h_lic_m)

            b_perfect = modelo.NewBoolVar(f'b_perfect_{emp.nombre}_{m_key}')
            b_high = modelo.NewBoolVar(f'b_high_{emp.nombre}_{m_key}')
            b_low = modelo.NewBoolVar(f'b_low_{emp.nombre}_{m_key}')

            modelo.Add(total_h >= min_h).OnlyEnforceIf(b_high)
            modelo.Add(total_h < min_h).OnlyEnforceIf(b_high.Not())
            modelo.Add(total_h <= max_h).OnlyEnforceIf(b_low)
            modelo.Add(total_h > max_h).OnlyEnforceIf(b_low.Not())

            modelo.AddBoolAnd([b_high, b_low]).OnlyEnforceIf(b_perfect)
            modelo.AddBoolOr([b_high.Not(), b_low.Not()]).OnlyEnforceIf(b_perfect.Not())

            ctx.bonuses_soft.append(b_perfect * bonus_val)
