"""
restricciones/soft/bonus_combo_finde.py — SOFT
Bonifica trabajar el mismo turno en sábado y domingo de una misma semana.
Regla: BONUS_COMBO_FINDE
"""
from datetime import date, timedelta
import rule_engine as _re


def apply(modelo, ctx):
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    dias_por_semana = {}
    for d in range(ctx.dias):
        lunes = (fecha_inicio_dt + timedelta(days=d))
        lunes = lunes - timedelta(days=lunes.weekday())
        dias_por_semana.setdefault(lunes.isoformat(), []).append(d)

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'BONUS_COMBO_FINDE', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_suspendida(params):
            continue
        for sem_key, dias_semana in dias_por_semana.items():
            sem_id = sem_key.replace('-', '_')
            sabados = [d for d in dias_semana if (d + ctx.offset_dia) % 7 == 5]
            domingos = [d for d in dias_semana if (d + ctx.offset_dia) % 7 == 6]
            if not sabados or not domingos:
                continue
            s, dom = sabados[0], domingos[0]
            for t_finde in ctx.demanda_turnos.get('Finde_Feriado', {}).keys():
                if (emp.nombre, s, t_finde) in ctx.turnos and \
                   (emp.nombre, dom, t_finde) in ctx.turnos:
                    combo = modelo.NewBoolVar(f'combo_{emp.nombre}_{sem_id}_{t_finde}')
                    modelo.AddMinEquality(
                        combo,
                        [ctx.turnos[(emp.nombre, s, t_finde)],
                         ctx.turnos[(emp.nombre, dom, t_finde)]]
                    )
                    ctx.bonuses_soft.append(combo)
